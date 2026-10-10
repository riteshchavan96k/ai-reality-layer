"""Step 223 — independent capture-time authority in strict Reality State freshness.

All observer callbacks here are FAKE and intentionally cannot establish
actual publisher TLS or factual truth. Step 222 keeps the separate live test.
"""

from dataclasses import replace
from datetime import datetime, timedelta, timezone
from hashlib import sha256
import json

import pytest
from fastapi.testclient import TestClient
from pydantic import ValidationError

from backend.app.api.evidence_reality_state import EvidenceRealityStateRequest
from backend.app.api.reality_state import RealityStateResponse
from backend.app.main import app
from backend.app.orchestrator.dependencies import OrchestrationDependencies
from backend.app.orchestrator.orchestrator import build_reality_state_from_evidence
from backend.app.reality.allowlisted_https_source_reader import AllowlistedHttpsSourceReader
from backend.app.reality.independent_source_text_assurance import IndependentSourceTextAssurance
from backend.app.reality.reality_state_builder import RealityStateBuilder
from backend.app.reality.source_freshness_evaluator import SourceFreshnessEvaluator


URI = "https://publisher.example.test/releases/python-3130"
ENTITY = "Python 3.13.0"
CONTENT = "Python 3.13.0 was released on October 7, 2024."


def stamp(dt):
    return dt.astimezone(timezone.utc).isoformat().replace("+00:00", "Z")


# Use the real wall clock minus a small margin so SourceObservation's canonical
# no-future guard remains satisfied regardless of host clock scheduling.
NOW = datetime.now(timezone.utc) - timedelta(seconds=5)
FRESH = stamp(NOW - timedelta(seconds=10))
STALE = stamp(NOW - timedelta(hours=3))
USER_OLD = stamp(NOW - timedelta(days=7))
USER_NEW = stamp(NOW - timedelta(seconds=1))


def reader(time=FRESH, *, uri=URI, content=CONTENT, metadata=True):
    def fetch(request_uri):
        result = {"uri": uri, "content": content}
        if metadata:
            result.update(
                capture_sha256=sha256(content.encode()).hexdigest(),
                capture_observed_at=time,
            )
        return result
    return fetch


def dependencies(read):
    return replace(
        OrchestrationDependencies.default(),
        independent_source_text_assurance=IndependentSourceTextAssurance(read),
        source_freshness_evaluator=SourceFreshnessEvaluator(clock=lambda: NOW),
        reality_state_builder=RealityStateBuilder(clock=lambda: NOW),
    )


def document(*, uri=URI, content=CONTENT, reported=None):
    item = {"uri": uri, "content": content}
    if reported is not None:
        item["observed_at"] = reported
    return item


def state(docs, read, *, strict=True, window=3600):
    output = build_reality_state_from_evidence(
        "What is Python 3.13.0's release date?", docs,
        entity=ENTITY,
        freshness_max_age_seconds=window,
        require_independent_source_text_match=strict,
        dependencies=dependencies(read),
    )
    RealityStateResponse.model_validate(output)
    return output


def observation(output):
    return output["source_observation"]["observations"][0]


def test_strict_capture_overrides_very_old_client_report_as_current_observation():
    result = state([document(reported=USER_OLD)], reader())
    assert result["status"] == "supported"
    assert observation(result)["observed_at"] == FRESH
    assert observation(result)["observation_method"] == "independent_source_capture"
    assert result["freshness"]["fresh_count"] == 1
    assert result["freshness"]["assessments"][0]["observed_at"] == FRESH
    assert result["evidence"]["independent_source_text_assurance"]["sources"][0]["capture_observed_at"] == FRESH
    assert result["evidence"]["independent_source_text_assurance"]["publisher_authenticated"] is False


def test_client_cannot_make_stale_independent_capture_appear_fresh():
    result = state([document(reported=USER_NEW)], reader(time=STALE))
    assert result["status"] == "uncertain"
    assert observation(result)["observation_method"] == "independent_source_capture"
    assert observation(result)["observed_at"] == STALE
    assert result["freshness"]["stale_count"] == 1
    assert "stale_sources_present" in result["confidence_signals"]["signals"]
    assert result["evidence"]["independent_source_text_assurance"]["status"] == "exact_text_observed"


def test_strict_backend_capture_does_not_need_a_caller_timestamp():
    request = EvidenceRealityStateRequest.model_validate({
        "task": "What is Python 3.13.0's release date?",
        "entity": ENTITY,
        "documents": [document()],
        "freshness_max_age_seconds": 3600,
        "require_independent_source_text_match": True,
    })
    assert request.documents[0].observed_at is None
    result = state([document()], reader())
    assert result["status"] == "supported"
    assert result["freshness"]["fresh_count"] == 1
    assert observation(result)["observation_method"] == "independent_source_capture"


def test_no_capture_no_submitted_observation_fails_closed_even_if_text_matches():
    result = state([document()], reader(metadata=False))
    assert result["status"] == "uncertain"
    assert result["source_observation"]["status"] == "unavailable"
    assert result["source_observation"]["reason"] == "independent_capture_observation_required"
    assert result["freshness"]["status"] == "unavailable"
    assert "freshness_unavailable" in result["confidence_signals"]["signals"]


def test_unconfigured_reader_missing_client_timestamp_stays_uncertain():
    result = state([document()], None)
    assert result["status"] == "uncertain"
    assert result["source_observation"]["status"] == "unavailable"
    assert result["evidence"]["independent_source_text_assurance"]["status"] == "unverified"


def test_legacy_operator_reader_with_reported_time_retains_replay_semantics():
    result = state([document(reported=USER_NEW)], reader(metadata=False))
    assert result["status"] == "supported"
    assert observation(result)["observed_at"] == USER_NEW
    assert observation(result)["observation_method"] == "submitted_evidence_observation"
    assert result["freshness"]["fresh_count"] == 1
    assert result["evidence"]["independent_source_text_assurance"]["publisher_authenticated"] is False


def test_opt_out_preserves_old_reported_source_timestamp():
    result = state([document(reported=USER_OLD)], reader(), strict=False)
    assert result["status"] == "uncertain"  # stale client timestamp
    assert observation(result)["observation_method"] == "submitted_evidence_observation"
    assert result["freshness"]["stale_count"] == 1
    assert "independent_source_text_assurance" not in result["evidence"]


def test_non_strict_freshness_still_requires_client_timestamp():
    with pytest.raises(ValidationError, match="requires observed_at"):
        EvidenceRealityStateRequest.model_validate({
            "task": "What is Python 3.13.0's release date?",
            "entity": ENTITY,
            "documents": [document()],
            "freshness_max_age_seconds": 3600,
        })
    with pytest.raises(ValueError, match="requires observed_at"):
        state([document()], reader(), strict=False)


@pytest.mark.parametrize("capture", [
    "not-a-dateZ", "", None, "2035-01-01T00:00:00Z",
])
def test_missing_invalid_future_backend_capture_never_uses_false_freshness(capture):
    result = state([document()], reader(time=capture))
    assert result["status"] == "uncertain"
    assert result["freshness"]["status"] == "unavailable"
    assert result["source_observation"]["status"] == "unavailable"


def test_two_sources_independent_observation_match_by_canonical_identity():
    uri2 = URI + "/more"
    text2 = "Python 3.13.0 is available now."
    def two(uri):
        content = CONTENT if uri == URI else text2
        return {
            "uri": uri, "content": content,
            "capture_sha256": sha256(content.encode()).hexdigest(),
            "capture_observed_at": FRESH if uri == URI else STALE,
        }
    result = state([
        document(uri=uri2, content=text2, reported=USER_NEW),
        document(uri=URI, reported=USER_NEW),
    ], two)
    assert result["status"] == "uncertain"
    assert result["freshness"]["fresh_count"] == 1
    assert result["freshness"]["stale_count"] == 1
    actual = {
        row["source_id"]: row
        for row in result["source_observation"]["observations"]
    }
    for source in result["source_provenance"]["sources"]:
        expected = STALE if source["uri"] == uri2 else FRESH
        assert actual[source["source_id"]]["observed_at"] == expected
        assert actual[source["source_id"]]["observation_method"] == "independent_source_capture"


def test_strict_actual_http_endpoint_accepts_missing_client_observed_at(monkeypatch):
    monkeypatch.setenv("ARL_INDEPENDENT_SOURCE_ALLOWED_URLS", json.dumps([URI]))
    calls = []
    def fake_network(self, uri):
        calls.append(uri)
        return reader()(uri)
    monkeypatch.setattr(AllowlistedHttpsSourceReader, "__call__", fake_network)
    with TestClient(app) as client:
        response = client.post("/api/v1/reality-state/evidence", json={
            "task": "What is Python 3.13.0's release date?",
            "entity": ENTITY,
            "documents": [document()],
            "require_independent_source_text_match": True,
            "freshness_max_age_seconds": 3600,
        })
    assert response.status_code == 200
    obj = response.json()
    assert obj["status"] == "supported"
    assert obj["source_observation"]["observations"][0]["observation_method"] == "independent_source_capture"
    assert calls == [URI]


def test_capture_is_observation_time_not_publisher_publication_date():
    result = state([document(reported=USER_OLD)], reader())
    assert result["status"] == "supported"
    assert result["source_observation"]["observations"][0]["observed_at"] == FRESH
    assert "October 7, 2024" in result["evidence"]["content"]
    assert result["evidence"]["independent_source_text_assurance"]["semantic_support_verified"] is False
