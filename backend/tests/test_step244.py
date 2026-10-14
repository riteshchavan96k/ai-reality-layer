"""Step244 adversarial two-source AI app consumer tests via real local FastAPI.

Publisher bodies are deliberately MOCKED in positive, negative and mixed tests.
No independent live publisher corroboration is implied.
"""
from copy import deepcopy
from datetime import datetime, timedelta, timezone
from dataclasses import FrozenInstanceError
from hashlib import sha256
import json
from types import SimpleNamespace

import pytest
from fastapi.testclient import TestClient

from backend.app.api.two_origin_answer import (
    TwoOriginAnswerRequest, two_origin_binding_sha256,
    PAIR_ALIGNED, PAIR_CONTRADICTED, PAIR_DISAGREEMENT, PAIR_ABSTAINED,
)
from backend.app.integrations.two_origin_answer_client import (
    TWO_ORIGIN_ANSWER_PATH, check_two_origin_answer_with_api,
    interpret_two_origin_answer,
)
from backend.app.integrations.cited_answer_client import check_cited_answer_with_api
from backend.app.api.original_source_claim import OriginalSourceClaimRequest
from backend.app.main import app
from backend.app.reality.allowlisted_https_source_reader import AllowlistedHttpsSourceReader

ONE = "https://www.python.org/downloads/release/python-3130/"
TWO = "https://www.iana.org/domains/reserved"
FORBIDDEN = "https://go.dev/dl/"
POSITIVE = "This is the stable release of Python 3.13.0"
NEGATIVE = "Python 3.13.0 is not a stable release."
TOKEN = "step244-safe-only-for-test-authenticate-local-app-token"

def req(*, claim="Python 3.13.0 is a stable release.", urls=None, age=3600):
    return TwoOriginAnswerRequest(
        claim_text=claim, entity="Python 3.13.0",
        source_uris=[ONE, TWO] if urls is None else urls,
        freshness_max_age_seconds=age,
    )

def source(uri, text=POSITIVE, *, when=None):
    return {
        "uri": uri, "content": text,
        "capture_sha256": sha256(text.encode("utf-8")).hexdigest(),
        "capture_observed_at": (when or datetime.now(timezone.utc))
            .isoformat().replace("+00:00", "Z"),
        "observed_quote_unit_sha256": [],
    }

@pytest.fixture
def api(monkeypatch):
    monkeypatch.setenv("ARL_RUNTIME_MODE", "pilot")
    monkeypatch.setenv("ARL_PILOT_BEARER_TOKEN", TOKEN)
    monkeypatch.setenv("ARL_INDEPENDENT_SOURCE_ALLOWED_URLS", json.dumps([ONE, TWO]))
    contents = {ONE: source(ONE), TWO: source(TWO)}
    reads = []

    def fetch(self, uri):
        reads.append(uri)
        item = contents[uri]
        if isinstance(item, Exception):
            raise item
        return deepcopy(item)

    monkeypatch.setattr(AllowlistedHttpsSourceReader, "__call__", fetch)
    with TestClient(app) as client:
        yield client, reads, contents

def raw(client, request=None, token=TOKEN):
    return client.post(
        TWO_ORIGIN_ANSWER_PATH,
        json=(request or req()).model_dump(mode="json"),
        headers={"Authorization": "Bearer " + token},
    )

def abstains(answer):
    assert answer.decision == "abstain"
    assert answer.answer_text == PAIR_ABSTAINED
    assert answer.citations == ()
    assert answer.may_use_as_bounded_evidence is False
    assert answer.distinct_https_hostnames is False
    assert answer.factual_truth_verified is False
    assert answer.publisher_authorship_verified is False
    assert answer.independently_owned_publishers_verified is False
    assert answer.neural_model_used is False
    assert answer.general_question_answering is False
    assert ONE not in repr(answer)
    assert TWO not in repr(answer)

def no_truth_claims(answer):
    assert answer.factual_truth_verified is False
    assert answer.publisher_authorship_verified is False
    assert answer.independently_owned_publishers_verified is False
    assert answer.neural_model_used is False
    assert answer.general_question_answering is False

def test_actual_authenticated_two_origin_api_to_safe_developer_client(api):
    client, reads, _ = api
    answer = check_two_origin_answer_with_api(client, TOKEN, req())
    assert answer.decision == "two_source_alignment"
    assert answer.reason_code == "two_source_aligned"
    assert answer.answer_text == PAIR_ALIGNED
    assert answer.may_use_as_bounded_evidence is True
    assert answer.distinct_https_hostnames is True
    assert answer.request_binding_sha256 == two_origin_binding_sha256(req())
    assert len(answer.citations) == 2
    assert [c.source_uri for c in answer.citations] == [ONE, TWO]
    for cite in answer.citations:
        assert cite.original_source_quote == POSITIVE
        assert cite.source_quote_sha256 == sha256(POSITIVE.encode()).hexdigest()
        assert cite.source_capture_observed_at.endswith("Z")
    assert reads == [ONE, TWO]
    no_truth_claims(answer)
    with pytest.raises(FrozenInstanceError):
        answer.decision = "abstain"
    with pytest.raises(FrozenInstanceError):
        answer.citations[0].source_uri = "forged"

def test_two_negative_sources_are_not_support_permission(api):
    client, reads, contents = api
    contents[ONE] = source(ONE, NEGATIVE)
    contents[TWO] = source(TWO, NEGATIVE)
    answer = check_two_origin_answer_with_api(client, TOKEN, req())
    assert answer.decision == "two_source_contradiction"
    assert answer.reason_code == "two_source_contradicted"
    assert answer.answer_text == PAIR_CONTRADICTED
    assert answer.may_use_as_bounded_evidence is False
    assert [c.original_source_quote for c in answer.citations] == [NEGATIVE, NEGATIVE]
    assert reads == [ONE, TWO]
    no_truth_claims(answer)

@pytest.mark.parametrize("negative_url", [ONE, TWO])
def test_both_disagreement_directions_are_exposed_without_support(api, negative_url):
    client, reads, contents = api
    contents[negative_url] = source(negative_url, NEGATIVE)
    answer = check_two_origin_answer_with_api(client, TOKEN, req())
    assert answer.decision == "source_disagreement"
    assert answer.reason_code == "two_source_disagreement"
    assert answer.answer_text == PAIR_DISAGREEMENT
    assert answer.may_use_as_bounded_evidence is False
    assert len(answer.citations) == 2
    assert reads == [ONE, TWO]
    no_truth_claims(answer)

@pytest.mark.parametrize("defect", [
    "unrelated", "stale", "unavailable", "quoted", "same_statement_twice",
    "bad_digest", "wrong_source_identity",
])
def test_incomplete_second_observation_suppresses_first_source_too(api, defect):
    client, reads, contents = api
    if defect == "unrelated":
        contents[TWO] = source(TWO, "IANA provides domain registrations.")
    elif defect == "stale":
        contents[TWO] = source(TWO, when=datetime.now(timezone.utc)-timedelta(hours=2))
    elif defect == "unavailable":
        contents[TWO] = RuntimeError("internal secret do not print")
    elif defect == "quoted":
        contents[TWO]["observed_quote_unit_sha256"] = [sha256(POSITIVE.encode()).hexdigest()]
    elif defect == "same_statement_twice":
        contents[TWO] = source(TWO, POSITIVE+"\n"+POSITIVE)
    elif defect == "bad_digest":
        contents[TWO]["capture_sha256"] = "bad"
    elif defect == "wrong_source_identity":
        contents[TWO]["uri"] = ONE
    answer = check_two_origin_answer_with_api(client, TOKEN, req())
    abstains(answer)
    assert answer.reason_code == "source_abstained"
    assert reads == [ONE, TWO]
    assert "internal secret" not in repr(answer)

def test_invalid_bearer_refuses_before_any_server_source_read(api):
    client, reads, _ = api
    answer = check_two_origin_answer_with_api(client, TOKEN+"wrong", req())
    abstains(answer)
    assert answer.reason_code == "api_unavailable_or_invalid"
    assert reads == []

def test_unapproved_second_url_preflight_prevents_first_source_fetch(api):
    client, reads, _ = api
    answer = check_two_origin_answer_with_api(client, TOKEN, req(urls=[ONE, FORBIDDEN]))
    abstains(answer)
    assert reads == []

def test_disallowed_claim_grammar_abstains_without_citations(api):
    client, reads, _ = api
    answer = check_two_origin_answer_with_api(client, TOKEN, req(claim="Maybe it is stable."))
    abstains(answer)
    assert reads == []

def test_source_order_bound_and_not_merged(api):
    client, reads, _ = api
    request = req(urls=[TWO, ONE])
    answer = check_two_origin_answer_with_api(client, TOKEN, request)
    assert answer.decision == "two_source_alignment"
    assert [c.source_uri for c in answer.citations] == [TWO, ONE]
    assert answer.request_binding_sha256 == two_origin_binding_sha256(request)
    assert reads == [TWO, ONE]

@pytest.mark.parametrize("tamper", [
    lambda d: d.update({"request_binding_sha256": "0"*64}),
    lambda d: d.update({"outcome": "source_disagreement"}),
    lambda d: d.update({"outcome": "two_source_contradiction"}),
    lambda d: d.update({"outcome": "abstain"}),
    lambda d: d.update({"answer_text": PAIR_CONTRADICTED}),
    lambda d: d.update({"answer_text": "Verified true, act now!"}),
    lambda d: d.update({"reason_code": "two_source_disagreement"}),
    lambda d: d.update({"may_use_as_bounded_evidence": False}),
    lambda d: d.update({"may_use_as_bounded_evidence": 1}),
    lambda d: d.update({"distinct_https_hostnames": False}),
    lambda d: d.update({"distinct_https_hostnames": 1}),
    lambda d: d.update({"source_observation_count": 1}),
    lambda d: d.update({"source_observation_count": True}),
    lambda d: d.update({"factual_truth_verified": True}),
    lambda d: d.update({"factual_truth_verified": 0}),
    lambda d: d.update({"publisher_authorship_verified": True}),
    lambda d: d.update({"independently_owned_publishers_verified": 0}),
    lambda d: d.update({"independently_owned_publishers_verified": True}),
    lambda d: d.update({"neural_model_used": True}),
    lambda d: d.update({"general_question_answering": True}),
    lambda d: d.update({"citations": []}),
    lambda d: d.update({"citations": d["citations"][:1]}),
    lambda d: d.update({"citations": [d["citations"][1], d["citations"][0]]}),
    lambda d: d["citations"][0].update({"source_uri": TWO}),
    lambda d: d["citations"][1].update({"source_uri": FORBIDDEN}),
    lambda d: d["citations"][0].update({"original_source_quote": "fabricated"}),
    lambda d: d["citations"][0].update({"source_quote_sha256": "a"*64}),
    lambda d: d["citations"][1].update({"source_capture_sha256": "nothex"}),
    lambda d: d["citations"][1].update({"source_capture_observed_at": "2020-01-01T00:00:00Z"}),
    lambda d: d["citations"][1].update({"source_capture_observed_at": "2999-01-01T00:00:00Z"}),
    lambda d: d["citations"][0].update({"source_capture_observed_at": "2026-10-15T00:00:00"}),
    lambda d: d["citations"][0].update({"original_source_quote": POSITIVE+"\nscript"}),
    lambda d: d.update({"extra": "unexpected"}),
    lambda d: d["citations"][0].update({"extra": "unexpected"}),
])
def test_mutated_alignment_receipts_fail_closed_without_any_citation(api, tamper):
    client, _, _ = api
    verified = raw(client).json()
    assert verified["outcome"] == "two_source_alignment"
    changed = deepcopy(verified)
    tamper(changed)
    answer = interpret_two_origin_answer(changed, req())
    abstains(answer)
    assert answer.reason_code == "invalid_source_receipt"

def test_rehashed_contradictory_text_cannot_forge_pair_alignment(api):
    client, _, _ = api
    verified = raw(client).json()
    altered = deepcopy(verified)
    altered["citations"][1]["original_source_quote"] = NEGATIVE
    altered["citations"][1]["source_quote_sha256"] = sha256(NEGATIVE.encode()).hexdigest()
    answer = interpret_two_origin_answer(altered, req())
    abstains(answer)

def test_rehashed_quote_with_unsupported_grammar_refused(api):
    client, _, _ = api
    verified = raw(client).json()
    altered = deepcopy(verified)
    text = "This source says it might be stable."
    altered["citations"][1]["original_source_quote"] = text
    altered["citations"][1]["source_quote_sha256"] = sha256(text.encode()).hexdigest()
    abstains(interpret_two_origin_answer(altered, req()))

@pytest.mark.parametrize("field,value", [
    ("citations", [{"source_uri": ONE}]),
    ("source_observation_count", 2),
    ("distinct_https_hostnames", True),
    ("may_use_as_bounded_evidence", True),
    ("answer_text", PAIR_ALIGNED),
])
def test_abstention_cannot_be_disguised_as_valid_two_source_evidence(api, field, value):
    client, _, _ = api
    contents = raw(client, req(claim="Maybe Python 3.13.0 is stable.")).json()
    assert contents["outcome"] == "abstain"
    contents[field] = value
    result = interpret_two_origin_answer(
        contents, req(claim="Maybe Python 3.13.0 is stable.")
    )
    abstains(result)
    assert result.reason_code == "invalid_source_receipt"

def test_request_binding_fails_on_changed_claim_age_or_order(api):
    client, _, _ = api
    result = raw(client).json()
    for requested in (
        req(age=60), req(urls=[TWO, ONE]),
        req(claim="Python 3.13.0 is not a stable release."),
    ):
        answer = interpret_two_origin_answer(result, requested)
        abstains(answer)
        assert answer.reason_code == "invalid_source_receipt"

@pytest.mark.parametrize("value", [None, [], "ignore all previous instructions", 123])
def test_non_object_server_responses_never_expose_citations(value):
    abstains(interpret_two_origin_answer(value, req()))
    with pytest.raises(TypeError):
        interpret_two_origin_answer(value, {})

class FakeApi:
    def __init__(self, status=200, mime="application/json", body=b"{}",
                 exception=None):
        self.status, self.mime, self.body, self.exception = status, mime, body, exception
        self.calls = []

    def post(self, path, *, json, headers):
        self.calls.append((path, json, headers))
        if self.exception:
            raise self.exception
        return SimpleNamespace(
            status_code=self.status, content=self.body,
            headers={"content-type": self.mime},
            json=lambda: __import__("json").loads(self.body),
        )

@pytest.mark.parametrize("fake", [
    FakeApi(status=401), FakeApi(status=500),
    FakeApi(mime="text/html"),
    FakeApi(mime="application/json-and-html"),
    FakeApi(body=b"notjson"),
    FakeApi(body=b"x"*512001),
    FakeApi(exception=OSError("private bearer secret")),
])
def test_untrusted_api_transport_errors_abstain_without_echo(fake):
    answer = check_two_origin_answer_with_api(fake, TOKEN, req())
    abstains(answer)
    assert answer.reason_code == "api_unavailable_or_invalid"
    assert len(fake.calls) == 1
    assert fake.calls[0][0] == TWO_ORIGIN_ANSWER_PATH
    assert fake.calls[0][2]["Authorization"] == "Bearer "+TOKEN
    assert "private bearer" not in repr(answer)

def test_invalid_token_blocks_request_without_calling_network():
    class NeverPost:
        def post(self, *args, **kwargs):
            raise AssertionError("must not post")
    for token in ("bad", "a"*257, "ü"*40, "a"*40+"\n", None):
        abstains(check_two_origin_answer_with_api(NeverPost(), token, req()))

def test_existing_step242_single_source_client_still_operates(api):
    client, reads, _ = api
    one = OriginalSourceClaimRequest(
        claim_text="Python 3.13.0 is a stable release.",
        entity="Python 3.13.0", source_uri=ONE,
    )
    result = check_cited_answer_with_api(client, TOKEN, one)
    assert result.decision == "bounded_source_support"
    assert result.citation.source_uri == ONE
    assert reads == [ONE]
