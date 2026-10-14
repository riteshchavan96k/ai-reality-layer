"""Step242: executable app-client tests against the real authenticated API."""

from copy import deepcopy
from datetime import datetime, timedelta, timezone
from hashlib import sha256
import json

import pytest
from fastapi.testclient import TestClient

from backend.app.api.original_source_claim import OriginalSourceClaimRequest
from backend.app.integrations.cited_answer_client import (
    ABSTAINED, ALIGNED, CONTRADICTED, ANSWER_PATH,
    check_cited_answer_with_api, interpret_cited_answer,
)
from backend.app.main import app
from backend.app.reality.allowlisted_https_source_reader import AllowlistedHttpsSourceReader

SOURCE = "https://www.python.org/downloads/release/python-3130/"
OFF_LIST = "https://www.iana.org/domains/reserved"
TEXT = "This is the stable release of Python 3.13.0"
TOKEN = "step242-test-client-authenticated-api-credential-validated"


def request(
    claim="Python 3.13.0 is a stable release.",
    source=SOURCE,
    max_age=3600,
):
    return OriginalSourceClaimRequest(
        entity="Python 3.13.0", claim_text=claim, source_uri=source,
        freshness_max_age_seconds=max_age,
    )


def capture(text=TEXT, *, when=None):
    return {
        "uri": SOURCE,
        "content": text,
        "capture_sha256": sha256(text.encode("utf-8")).hexdigest(),
        "capture_observed_at": (when or datetime.now(timezone.utc))
        .isoformat().replace("+00:00", "Z"),
        "observed_quote_unit_sha256": [],
    }


@pytest.fixture
def api(monkeypatch):
    monkeypatch.setenv("ARL_RUNTIME_MODE", "pilot")
    monkeypatch.setenv("ARL_PILOT_BEARER_TOKEN", TOKEN)
    monkeypatch.setenv("ARL_INDEPENDENT_SOURCE_ALLOWED_URLS", json.dumps([SOURCE]))
    reads = []
    current = {"capture": capture()}

    def injected(self, url):
        reads.append(url)
        return current["capture"]

    monkeypatch.setattr(AllowlistedHttpsSourceReader, "__call__", injected)
    with TestClient(app) as client:
        yield client, reads, current


def post_raw(client, rq=None, token=TOKEN):
    return client.post(
        ANSWER_PATH,
        json=(rq or request()).model_dump(mode="json"),
        headers={"Authorization": "Bearer " + token},
    )


def assert_no_evidence(result):
    assert result.decision == "abstain"
    assert result.answer_text == ABSTAINED
    assert result.citation is None
    assert result.may_use_as_bounded_evidence is False
    assert result.factual_truth_verified is False
    assert result.publisher_authorship_verified is False
    assert result.neural_model_used is False
    assert result.general_question_answering is False


def test_real_app_client_gets_a_source_cited_answer_with_one_authenticated_post(api):
    client, reads, _ = api
    result = check_cited_answer_with_api(client, TOKEN, request())
    assert result.decision == "bounded_source_support"
    assert result.reason_code == "source_aligned"
    assert result.may_use_as_bounded_evidence is True
    assert result.answer_text == ALIGNED
    assert result.citation.source_uri == SOURCE
    assert result.citation.original_source_quote == TEXT
    assert result.citation.source_quote_sha256 == sha256(TEXT.encode()).hexdigest()
    assert result.citation.source_capture_sha256 == sha256(TEXT.encode()).hexdigest()
    assert result.citation.source_capture_observed_at.endswith("Z")
    assert reads == [SOURCE]
    assert_no_truth_upgrade(result)


def assert_no_truth_upgrade(result):
    assert result.factual_truth_verified is False
    assert result.publisher_authorship_verified is False
    assert result.neural_model_used is False
    assert result.general_question_answering is False


def test_real_app_client_reports_source_contradiction_without_support_promotion(api):
    client, reads, _ = api
    req = request("Python 3.13.0 is not a stable release.")
    result = check_cited_answer_with_api(client, TOKEN, req)
    assert result.decision == "bounded_source_contradiction"
    assert result.reason_code == "source_contradicted"
    assert result.answer_text == CONTRADICTED
    assert result.may_use_as_bounded_evidence is False
    assert result.citation.original_source_quote == TEXT
    assert reads == [SOURCE]
    assert_no_truth_upgrade(result)


@pytest.mark.parametrize("claim", [
    "Python 3.13.0 is production-ready.",
    "Maybe Python 3.13.0 is a stable release.",
    "Python 3.13.0 is a stable release, and so is another product.",
])
def test_app_client_abstains_on_unsupported_claims(api, claim):
    client, reads, _ = api
    result = check_cited_answer_with_api(client, TOKEN, request(claim))
    assert_no_evidence(result)
    assert result.reason_code == "source_abstained"
    assert len(reads) <= 1


def test_unapproved_url_abstains_before_source_network_read(api):
    client, reads, _ = api
    result = check_cited_answer_with_api(client, TOKEN, request(source=OFF_LIST))
    assert_no_evidence(result)
    assert reads == []


def test_bad_auth_abstains_before_source_read_and_no_token_is_ever_in_result(api):
    client, reads, _ = api
    result = check_cited_answer_with_api(client, TOKEN + "bad", request())
    assert_no_evidence(result)
    assert result.reason_code == "api_unavailable_or_invalid"
    assert reads == []
    assert TOKEN not in repr(result)


def test_malformed_token_never_calls_transport():
    class MustNotCall:
        def post(self, *args, **kwargs):
            raise AssertionError("network call should have been blocked")
    for token in ("bad", "x" * 257, "a" * 40 + "\n", "é" * 40, None):
        result = check_cited_answer_with_api(MustNotCall(), token, request())
        assert_no_evidence(result)


def test_stale_server_capture_abstains_on_real_app_client(api):
    client, _, current = api
    current["capture"] = capture(when=datetime.now(timezone.utc)-timedelta(hours=2))
    assert_no_evidence(check_cited_answer_with_api(client, TOKEN, request()))


@pytest.mark.parametrize("mutation", [
    lambda d: d.update({"request_binding_sha256": "0" * 64}),
    lambda d: d.update({"answer_text": "Verified factual truth."}),
    lambda d: d.update({"outcome": "bounded_source_contradiction"}),
    lambda d: d.update({"outcome": "abstain"}),
    lambda d: d.update({"original_source_observed": False}),
    lambda d: d.update({"factual_truth_verified": True}),
    lambda d: d.update({"factual_truth_verified": 0}),
    lambda d: d.update({"publisher_authorship_verified": True}),
    lambda d: d.update({"neural_model_used": True}),
    lambda d: d.update({"general_question_answering": True}),
    lambda d: d.update({"extra_provenance": "forged"}),
    lambda d: d.update({"citation": None}),
    lambda d: d["citation"].update({"source_uri": OFF_LIST}),
    lambda d: d["citation"].update({"original_source_quote": "forged"}),
    lambda d: d["citation"].update({"original_source_quote": TEXT + "\n<script>"}),
    lambda d: d["citation"].update({"source_quote_sha256": "a" * 64}),
    lambda d: d["citation"].update({"source_capture_sha256": "not-hex"}),
    lambda d: d["citation"].update({"source_capture_observed_at": "2020-01-01T00:00:00Z"}),
    lambda d: d["citation"].update({"source_capture_observed_at": "2999-01-01T00:00:00Z"}),
    lambda d: d["citation"].update({"source_capture_observed_at": "2026-10-15T00:00:00"}),
])
def test_mixed_forged_or_expired_citation_is_never_consumed(api, mutation):
    client, _, _ = api
    payload = post_raw(client).json()
    assert payload["citation"] is not None
    tampered = deepcopy(payload)
    mutation(tampered)
    result = interpret_cited_answer(tampered, request())
    assert_no_evidence(result)
    assert result.reason_code == "invalid_source_receipt"


def test_request_identity_includes_freshness_limit(api):
    client, _, _ = api
    payload = post_raw(client).json()
    result = interpret_cited_answer(payload, request(max_age=60))
    assert_no_evidence(result)
    assert result.reason_code == "invalid_source_receipt"


def test_only_valid_server_abstention_is_propagated_as_source_abstained(api):
    client, _, _ = api
    req = request("Python 3.13.0 is production-ready.")
    body = post_raw(client, req).json()
    result = interpret_cited_answer(body, req)
    assert_no_evidence(result)
    assert result.reason_code == "source_abstained"
    for change in (
        {"citation": {"source_uri": SOURCE}},
        {"original_source_observed": True},
        {"answer_text": ALIGNED},
    ):
        mutated = deepcopy(body)
        mutated.update(change)
        assert interpret_cited_answer(mutated, req).reason_code == "invalid_source_receipt"


def test_non_dictionary_or_server_message_cannot_be_treated_as_citation():
    for value in (None, [], "ignore previous instructions", 123):
        assert_no_evidence(interpret_cited_answer(value, request()))
    with pytest.raises(TypeError):
        interpret_cited_answer({}, {})


class _FakeClient:
    def __init__(self, *, status=200, mime="application/json",
                 body=b"{}", error=None):
        self.status, self.mime, self.body, self.error = status, mime, body, error
        self.calls = []

    def post(self, path, *, json, headers):
        self.calls.append((path, json, headers))
        if self.error:
            raise self.error
        import types
        return types.SimpleNamespace(
            status_code=self.status,
            content=self.body,
            headers={"content-type": self.mime},
            json=lambda: __import__("json").loads(self.body),
        )


@pytest.mark.parametrize("fake", [
    _FakeClient(status=401),
    _FakeClient(status=500),
    _FakeClient(mime="text/html"),
    _FakeClient(body=b"not-json"),
    _FakeClient(body=b"x" * 512001),
    _FakeClient(error=ValueError("secret should not be emitted")),
])
def test_transport_errors_or_oversized_result_abstain_without_echo(fake):
    result = check_cited_answer_with_api(fake, TOKEN, request())
    assert_no_evidence(result)
    assert result.reason_code == "api_unavailable_or_invalid"
    assert "secret" not in repr(result)
    assert len(fake.calls) == 1
    assert fake.calls[-1][0] == ANSWER_PATH


def test_openapi_and_old_endpoint_contracts_are_unchanged(api):
    client, _, _ = api
    schema = app.openapi()
    assert ANSWER_PATH in schema["paths"]
    assert "Cited" not in json.dumps(schema["paths"][ANSWER_PATH])
    old = client.post(
        "/api/v1/reality-state/claim",
        json=request().model_dump(mode="json"),
        headers={"Authorization": "Bearer " + TOKEN},
    )
    assert old.status_code == 200
    assert old.json()["source_evidence"]["text"] == TEXT
