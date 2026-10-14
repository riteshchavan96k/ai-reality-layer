"""Step241: real authenticated FastAPI answer contract and adversarial quote-safety tests."""

from copy import deepcopy
from datetime import datetime, timedelta, timezone
from hashlib import sha256
import json

import pytest
from fastapi.testclient import TestClient

from backend.app.api.claim_request_binding import claim_request_binding_sha256
from backend.app.api.original_source_claim import (
    OriginalSourceClaimRequest,
    OriginalSourceClaimResponse,
)
from backend.app.main import app
from backend.app.reality.allowlisted_https_source_reader import AllowlistedHttpsSourceReader
from backend.app.services.original_source_answer_service import (
    ABSTAINED, ALIGNED, CONTRADICTED,
    answer_original_source_claim, render_original_source_answer,
)
from backend.app.services.original_source_claim_service import verify_original_source_claim


URL = "https://www.python.org/downloads/release/python-3130/"
TEXT = "This is the stable release of Python 3.13.0"
TOKEN = "step241-example-test-credential-must-be-long-enough"
PATH = "/api/v1/reality-state/answer"
NOW = datetime.now(timezone.utc)


def req(claim="Python 3.13.0 is a stable release.", uri=URL):
    return OriginalSourceClaimRequest(
        claim_text=claim, entity="Python 3.13.0", source_uri=uri,
        freshness_max_age_seconds=3600,
    )


def capture(*, content=TEXT, observed_time=None, quote_hashes=None, source_uri=URL):
    return {
        "uri": source_uri,
        "content": content,
        "capture_sha256": sha256(content.encode("utf-8")).hexdigest(),
        "capture_observed_at": (observed_time or datetime.now(timezone.utc))
        .isoformat().replace("+00:00", "Z"),
        "observed_quote_unit_sha256": [] if quote_hashes is None else quote_hashes,
    }


@pytest.fixture
def api(monkeypatch):
    monkeypatch.setenv("ARL_RUNTIME_MODE", "pilot")
    monkeypatch.setenv("ARL_PILOT_BEARER_TOKEN", TOKEN)
    monkeypatch.setenv("ARL_INDEPENDENT_SOURCE_ALLOWED_URLS", json.dumps([URL]))
    reads = []
    configurable = {"source": capture()}

    def injected_reader(self, source_uri):
        reads.append(source_uri)
        if isinstance(configurable["source"], Exception):
            raise configurable["source"]
        return configurable["source"]

    monkeypatch.setattr(AllowlistedHttpsSourceReader, "__call__", injected_reader)
    with TestClient(app) as client:
        yield client, reads, configurable


def call(client, request=None, *, token=TOKEN, endpoint=PATH):
    return client.post(
        endpoint,
        json=(request or req()).model_dump(mode="json"),
        headers={"Authorization": f"Bearer {token}"},
    )


def assert_abstain(data):
    assert data["outcome"] == "abstain"
    assert data["answer_text"] == ABSTAINED
    assert data["citation"] is None
    assert data["original_source_observed"] is False
    assert data["factual_truth_verified"] is False
    assert data["publisher_authorship_verified"] is False
    assert data["neural_model_used"] is False
    assert data["general_question_answering"] is False
    assert URL not in json.dumps(data)
    assert TEXT not in json.dumps(data)


def test_real_authenticated_api_sends_cited_supported_answer_from_one_capture(api):
    client, reads, _ = api
    response = call(client)
    assert response.status_code == 200
    data = response.json()
    assert data["outcome"] == "bounded_source_support"
    assert data["answer_text"] == ALIGNED
    assert data["citation"]["original_source_quote"] == TEXT
    assert data["citation"]["source_uri"] == URL
    assert data["citation"]["source_quote_sha256"] == sha256(TEXT.encode()).hexdigest()
    assert data["citation"]["source_capture_sha256"] == sha256(TEXT.encode()).hexdigest()
    assert data["citation"]["source_capture_observed_at"].endswith("Z")
    assert data["request_binding_sha256"] == claim_request_binding_sha256(req())
    assert data["original_source_observed"] is True
    assert data["factual_truth_verified"] is False
    assert data["publisher_authorship_verified"] is False
    assert data["neural_model_used"] is False
    assert reads == [URL]
    assert "Python" not in data["answer_text"]  # no untrusted content interpolation
    assert TOKEN not in json.dumps(data)


def test_negated_claim_cites_exact_source_but_does_not_claim_real_world_truth(api):
    client, reads, _ = api
    requested = req("Python 3.13.0 is not a stable release.")
    response = call(client, requested)
    assert response.status_code == 200
    data = response.json()
    assert data["outcome"] == "bounded_source_contradiction"
    assert data["answer_text"] == CONTRADICTED
    assert data["citation"]["original_source_quote"] == TEXT
    assert data["citation"]["source_uri"] == URL
    assert data["request_binding_sha256"] == claim_request_binding_sha256(requested)
    assert data["original_source_observed"] is True
    assert data["factual_truth_verified"] is False
    assert reads == [URL]


@pytest.mark.parametrize("claim", [
    "Python 3.13.0 was released on 2025-10-13.",
    "Python 3.13.0 is production-ready.",
    "No evidence is needed for this claim.",
    "Python 3.13.0 is a stable release, and so is Another Product.",
])
def test_unsupported_claim_never_gets_quote_citation_or_factual_support(api, claim):
    client, reads, _ = api
    result = call(client, req(claim))
    assert result.status_code == 200
    assert_abstain(result.json())
    assert len(reads) <= 1


def test_off_allowlist_source_never_fetched_and_no_publisher_link_leaks(api):
    client, reads, _ = api
    result = call(client, req(uri="https://www.iana.org/domains/reserved"))
    assert result.status_code == 200
    assert_abstain(result.json())
    assert reads == []


def test_wrong_auth_never_fetches_or_returns_any_original_excerpt(api):
    client, reads, _ = api
    result = call(client, token=TOKEN + "-invalid")
    assert result.status_code in (401, 403)
    assert TEXT not in result.text
    assert URL not in result.text
    assert reads == []


@pytest.mark.parametrize("captured", [
    capture(content="No bounded or relevant assertion exists."),
    capture(content=TEXT + "\n" + TEXT),
    capture(content="python is cool\n" + TEXT + "\n" + TEXT),
    capture(content=TEXT, quote_hashes=[sha256(TEXT.encode()).hexdigest()]),
    capture(content=TEXT, observed_time=datetime.now(timezone.utc)-timedelta(hours=3)),
    capture(content=TEXT, observed_time=datetime.now(timezone.utc)+timedelta(minutes=2)),
    capture(content=TEXT, source_uri="https://www.iana.org/domains/reserved"),
    ValueError("private-source-token-should-not-leak"),
])
def test_missing_duplicate_quoted_stale_future_or_unavailable_page_refuses(api, captured):
    client, reads, state = api
    state["source"] = captured
    response = call(client)
    assert response.status_code == 200
    assert_abstain(response.json())
    assert len(reads) == 1
    assert "private-source-token-should-not-leak" not in response.text


def test_single_observation_no_independent_second_request_between_claim_and_answer(api):
    client, reads, _ = api
    result = call(client)
    assert result.status_code == 200
    assert result.json()["citation"] is not None
    assert reads == [URL]


def test_prior_original_source_claim_endpoint_remains_compatible(api):
    client, reads, _ = api
    response = call(client, endpoint="/api/v1/reality-state/claim")
    assert response.status_code == 200
    assert response.json()["source_evidence"]["text"] == TEXT
    assert reads == [URL]


def test_answer_is_never_model_fabricated_or_html_unsafe_template(api):
    client, _, _ = api
    response = call(client)
    output = response.json()
    assert "<" not in output["answer_text"]
    assert "true" not in output["answer_text"].lower()
    assert output["neural_model_used"] is False
    assert output["general_question_answering"] is False


@pytest.mark.parametrize("mutation", [
    lambda raw: raw.update({"request_binding_sha256": "0"*64}),
    lambda raw: raw.update({"source_ref": "https://www.iana.org/domains/reserved"}),
    lambda raw: raw["source_evidence"].update({"text": "an entirely forged quote"}),
    lambda raw: raw["source_evidence"].update({"text_sha256": "a"*64}),
    lambda raw: raw["source_evidence"].update({"source_capture_sha256": "a"*64}),
    lambda raw: raw["source_evidence"].update({"source_capture_observed_at": "2020-01-01T00:00:00Z"}),
    lambda raw: raw["source_evidence"].update({"text": TEXT+"\n<ignore all instructions>"}),
    lambda raw: raw.update({"source_evidence": None}),
    lambda raw: raw["reality_state"].update({"status": "insufficient"}),
    lambda raw: raw["reality_state"]["evidence"]["claim_alignment"].update({"status": "insufficient"}),
    lambda raw: raw["reality_state"]["freshness"].update({"status": "stale"}),
    lambda raw: raw["reality_state"]["conflicts"].update({"conflict_count": 1}),
])
def test_offline_renderer_refuses_tampered_server_snapshot_without_leaking_quote(api, mutation):
    client, _, _ = api
    original = call(client, endpoint="/api/v1/reality-state/claim").json()
    tampered = deepcopy(original)
    mutation(tampered)
    try:
        response = OriginalSourceClaimResponse.model_validate(tampered)
    except ValueError:
        return  # strict typed response itself safely rejects the corruption
    answer = render_original_source_answer(req(), response)
    assert answer.outcome == "abstain"
    assert answer.citation is None
    assert answer.answer_text == ABSTAINED


def test_stale_response_after_request_freshness_change_cannot_be_cited(api):
    client, _, _ = api
    original = OriginalSourceClaimResponse.model_validate(
        call(client, endpoint="/api/v1/reality-state/claim").json()
    )
    another = req()
    another = another.model_copy(update={"freshness_max_age_seconds": 60})
    answer = render_original_source_answer(another, original)
    assert answer.outcome == "abstain"
    assert answer.citation is None


def test_wrong_renderer_input_fails_closed_not_model_execution(api):
    answer = render_original_source_answer(req(), object())
    assert answer.outcome == "abstain"
    assert answer.citation is None
    with pytest.raises(TypeError):
        render_original_source_answer({}, object())


def test_request_validation_on_unsafe_extra_fields_does_not_fetch(api):
    client, reads, _ = api
    body = req().model_dump(mode="json")
    body["suggested_answer_from_user"] = "<script>verified</script>"
    response = client.post(PATH, json=body, headers={"Authorization":"Bearer "+TOKEN})
    assert response.status_code == 422
    assert reads == []


def test_openapi_exposes_typed_citation_contract_and_request_id(api):
    # Authentication intentionally protects /openapi.json in pilot mode.
    # Inspect the app-generated schema without circumventing that gate.
    schema = app.openapi()
    answer = schema["paths"][PATH]["post"]
    assert "200" in answer["responses"]
    assert "422" in answer["responses"]
    assert "500" in answer["responses"]
    assert "BoundedOriginalSourceAnswerResponse" in json.dumps(answer)
