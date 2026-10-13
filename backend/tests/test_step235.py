"""Step 235 safe downstream AI-consumer tests using the real pilot FastAPI.

Only remote publisher reading is replaced by a fixed observation. Additional
tampering tests mutate actual outputs, not fabricated 'success' fixture data.
"""
from copy import deepcopy
from datetime import datetime, timedelta, timezone
from hashlib import sha256
import json

import pytest
from fastapi.testclient import TestClient

from backend.app.api.claim_request_binding import claim_request_binding_sha256
from backend.app.api.original_source_claim import OriginalSourceClaimRequest
from backend.app.integrations.ai_claim_gate import (
    AIClaimGateDecision,
    check_claim_with_api,
    interpret_claim_reality_state,
)
from backend.app.main import app
from backend.app.reality.allowlisted_https_source_reader import AllowlistedHttpsSourceReader


URL = "https://www.python.org/downloads/release/python-3130/"
EXCERPT = "This is the stable release of Python 3.13.0"
TOKEN = "strict-local-consumer-integration-token-for-tests"


def claim_request(claim="Python 3.13.0 is a stable release.", **kwargs):
    return OriginalSourceClaimRequest(
        claim_text=claim, entity="Python 3.13.0", source_uri=URL, **kwargs
    )


@pytest.fixture
def api(monkeypatch):
    monkeypatch.setenv("ARL_RUNTIME_MODE", "pilot")
    monkeypatch.setenv("ARL_PILOT_BEARER_TOKEN", TOKEN)
    monkeypatch.setenv("ARL_INDEPENDENT_SOURCE_ALLOWED_URLS", json.dumps([URL]))
    calls = []

    def reader(self, uri):
        calls.append(uri)
        return {
            "uri": uri,
            "content": EXCERPT,
            "capture_sha256": sha256(EXCERPT.encode("utf-8")).hexdigest(),
            "capture_observed_at": datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"),
            "observed_quote_unit_sha256": [],
        }

    monkeypatch.setattr(AllowlistedHttpsSourceReader, "__call__", reader)
    with TestClient(app) as client:
        yield client, calls


def real_payload(client, request):
    reply = client.post(
        "/api/v1/reality-state/claim",
        json=request.model_dump(mode="json"),
        headers={"Authorization": "Bearer " + TOKEN},
    )
    assert reply.status_code == 200, reply.text
    return reply.json()


def test_actual_authenticated_client_uses_one_source_capture_for_bounded_support(api):
    client, calls = api
    result = check_claim_with_api(client, TOKEN, claim_request())
    assert result.decision == "bounded_supported"
    assert result.may_use_as_bounded_evidence is True
    assert result.reason_code == "bounded_source_alignment"
    assert result.semantic_truth_verified is False
    assert result.publisher_authorship_verified is False
    assert result.source_ref == URL
    assert len(result.capture_sha256) == 64
    assert result.capture_observed_at.endswith("Z")
    assert calls == [URL]
    assert TOKEN not in repr(result)
    assert EXCERPT not in repr(result)


def test_negated_claim_is_bounded_source_contradiction_not_general_falsehood(api):
    client, calls = api
    result = check_claim_with_api(
        client, TOKEN, claim_request("Python 3.13.0 is not a stable release.")
    )
    assert result.decision == "bounded_contradicted"
    assert result.may_use_as_bounded_evidence is False
    assert result.reason_code == "bounded_source_contradiction"
    assert result.semantic_truth_verified is False
    assert calls == [URL]


def test_wrong_or_missing_auth_never_fetches_source(api):
    client, calls = api
    assert check_claim_with_api(client, TOKEN + "wrong", claim_request()).decision == "abstain"
    assert check_claim_with_api(client, "short", claim_request()).decision == "abstain"
    assert calls == []


def test_request_binding_stable_for_equivalent_validated_input_and_changes_for_other_claim():
    original = claim_request()
    assert claim_request_binding_sha256(original) == claim_request_binding_sha256(claim_request())
    assert claim_request_binding_sha256(original) != claim_request_binding_sha256(
        claim_request("Python 3.13.0 is not a stable release.")
    )
    assert len(claim_request_binding_sha256(original)) == 64


@pytest.mark.parametrize("path,value", [
    (("request_binding_sha256",), "0"*64),
    (("source_ref",), "https://www.iana.org/domains/reserved"),
    (("status",), "supported-but-untrusted"),
    (("reason",), "source_unavailable"),
    (("reality_state","status"), "uncertain"),
    (("reality_state","entity","name"), "Python 3.12.0"),
    (("reality_state","verification","status"), "not_completed"),
    (("reality_state","confidence_signals","status"), "uncertain"),
    (("reality_state","freshness","status"), "unavailable"),
    (("reality_state","freshness","stale_count"), 1),
    (("reality_state","conflicts","conflict_count"), 1),
    (("reality_state","evidence","claim_alignment","status"), "contradicted"),
    (("reality_state","evidence","claim_alignment","factual_truth_verified"), True),
    (("reality_state","evidence","claim_alignment","semantic_support_verified"), True),
    (("reality_state","evidence","claim_alignment","source_count"), 2),
    (("reality_state","evidence","claim_alignment","decision_reasons"), []),
    (("reality_state","evidence","independent_source_text_assurance","source_count"), 2),
    (("reality_state","evidence","independent_source_text_assurance","publisher_authenticated"), True),
    (("reality_state","evidence","independent_source_text_assurance","sources"), []),
    (("reality_state","evidence","independent_source_text_assurance","sources",0,"capture_sha256"), "invalid"),
    (("reality_state","evidence","independent_source_text_assurance","sources",0,"source_ref"), "https://www.iana.org/domains/reserved"),
    (("reality_state","evidence","independent_source_text_assurance","sources",0,"source_quote_context_status"), "quoted_source_unit"),
    (("reality_state","evidence","independent_source_text_assurance","sources",0,"source_counterstatement_status"), "counterstatement_observed"),
    (("reality_state","evidence","independent_source_text_assurance","sources",0,"assertion_context_status"), "unverified"),
])
def test_real_supported_response_cannot_survive_inconsistent_or_tampered_field(api, path, value):
    client, _ = api
    req = claim_request()
    original = real_payload(client, req)
    result = deepcopy(original)
    slot = result
    for key in path[:-1]:
        slot = slot[key]
    slot[path[-1]] = value
    outcome = interpret_claim_reality_state(result, req)
    assert outcome.decision == "abstain"
    assert outcome.may_use_as_bounded_evidence is False
    assert outcome.capture_sha256 is None


def test_replayed_supported_response_cannot_authorize_different_claim_or_entity(api):
    client, _ = api
    result = real_payload(client, claim_request())
    opposite = claim_request("Python 3.13.0 is not a stable release.")
    assert interpret_claim_reality_state(result, opposite).decision == "abstain"
    wrong_entity = OriginalSourceClaimRequest(
        claim_text=claim_request().claim_text, entity="Python 3.12.0", source_uri=URL
    )
    assert interpret_claim_reality_state(result, wrong_entity).decision == "abstain"


@pytest.mark.parametrize("offset_seconds", [-7200, 7200])
def test_old_or_future_capture_receipt_fails_even_if_server_labels_supported(api, offset_seconds):
    client, _ = api
    req = claim_request()
    value = real_payload(client, req)
    value["reality_state"]["evidence"]["independent_source_text_assurance"]["sources"][0][
        "capture_observed_at"
    ] = (datetime.now(timezone.utc) + timedelta(seconds=offset_seconds)).isoformat().replace(
        "+00:00", "Z"
    )
    assert interpret_claim_reality_state(value, req).decision == "abstain"


def test_missing_result_and_non_object_json_abstain_without_throwing(api):
    client, _ = api
    req = claim_request()
    assert interpret_claim_reality_state({}, req).decision == "abstain"
    assert interpret_claim_reality_state([], req).decision == "abstain"
    assert interpret_claim_reality_state(None, req).decision == "abstain"


def test_wrong_url_never_fetches_even_if_client_supplies_exact_valid_https(api):
    client, calls = api
    req = OriginalSourceClaimRequest(
        claim_text="Python 3.13.0 is a stable release.",
        entity="Python 3.13.0", source_uri="https://www.python.org/unreviewed/",
    )
    result = check_claim_with_api(client, TOKEN, req)
    assert result.decision == "abstain"
    assert calls == []


class BrokenHttpTransport:
    def post(self, *args, **kwargs):
        raise RuntimeError("secret-bearing debug response MUST NOT escape")


def test_transport_exception_yields_fixed_safe_abstention():
    result = check_claim_with_api(BrokenHttpTransport(), TOKEN, claim_request())
    assert result == AIClaimGateDecision("abstain", False, "api_unavailable_or_invalid")
    assert "secret-bearing" not in repr(result)


def test_invalid_request_object_refused_before_transport_call(api):
    client, calls = api
    with pytest.raises(TypeError):
        check_claim_with_api(client, TOKEN, "an unvalidated user prompt")
    assert calls == []
