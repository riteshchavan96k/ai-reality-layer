"""Step 183 — explicit observation-age policy for retrieved sources."""

import json
from dataclasses import replace
from datetime import datetime, timezone

import pytest

from backend.app.api.reality_state import RealityStateRequest
from backend.app.main import app, reality_state
from backend.app.orchestrator.dependencies import OrchestrationDependencies
from backend.app.orchestrator.orchestrator import build_reality_state
from backend.app.reality.evidence_normalizer import RetrievalEvidenceNormalizer
from backend.app.reality.http_retrieval_provider import HttpRetrievalProvider
from backend.app.reality.source_freshness_evaluator import SourceFreshnessEvaluator
from backend.app.reality.source_observation import (
    SourceObservation,
    normalize_reported_observation_time,
)
from backend.app.reality.source_observation_builder import SourceObservationBuilder
from backend.app.reality.source_provenance_builder import SourceProvenanceBuilder


NOW = datetime(2026, 1, 1, 13, tzinfo=timezone.utc)
URI_A = "https://example.test/original-a"
URI_B = "https://example.test/original-b"
TEMPLATE = "https://retrieval.example.test/search?q={query}"


def _sources(*, older=False, partial=False):
    items = [
        {
            "uri": URI_A,
            "title": "A",
            "content": "Company X launched Feature A.",
            "observed_at": "2026-01-01T12:30:00Z",
        },
        {
            "uri": URI_B,
            "title": "B",
            "content": "Company X hired employees.",
            "observed_at": "2026-01-01T12:45:00Z",
        },
    ]
    if older:
        items[1]["observed_at"] = "2026-01-01T10:00:00Z"
    if partial:
        del items[1]["observed_at"]
    return items


def _deps():
    return replace(
        OrchestrationDependencies.default(),
        source_observation_builder=SourceObservationBuilder(clock=lambda: NOW),
        source_freshness_evaluator=SourceFreshnessEvaluator(clock=lambda: NOW),
    )


def _fake_http(monkeypatch, response):
    class Response:
        def __enter__(self):
            return self

        def __exit__(self, *args):
            return False

        def read(self, limit):
            raw = json.dumps(response).encode("utf-8")
            assert len(raw) <= limit
            return raw

    def fake_open(request, timeout):
        assert request.full_url.startswith(
            "https://retrieval.example.test/search?q="
        )
        assert timeout == 10.0
        return Response()

    monkeypatch.setenv("ARL_HTTP_RETRIEVAL_ENDPOINT_TEMPLATE", TEMPLATE)
    monkeypatch.setattr(
        "backend.app.reality.http_retrieval_provider.urlopen",
        fake_open,
    )


def _build(monkeypatch, sources, max_age=3600):
    _fake_http(monkeypatch, {"status": "completed", "sources": sources})
    return build_reality_state(
        "What is the current status of Company X?",
        dependencies=_deps(),
        freshness_max_age_seconds=max_age,
    )


@pytest.mark.parametrize(
    "value",
    [
        "2026-01-01T12:30:00",
        "not a timestamp",
        "",
        " ",
        None,
        123,
        "2999-01-01T00:00:00Z",
    ],
)
def test_reported_observation_timestamp_rejects_invalid_values(value):
    with pytest.raises(ValueError):
        normalize_reported_observation_time(value)


def test_reported_observation_normalizes_offset_to_utc():
    assert normalize_reported_observation_time(
        "2026-01-01T18:00:00+05:30"
    ) == "2026-01-01T12:30:00Z"


def test_retrieval_provider_observation_method_distinguishes_assurance():
    item = SourceObservation(
        "source-id",
        "2026-01-01T12:30:00Z",
        observation_method="retrieval_provider_observation",
    )
    assert item.to_dict()["observation_method"] == (
        "retrieval_provider_observation"
    )
    with pytest.raises(ValueError, match="observation_method"):
        SourceObservation(
            "source-id",
            "2026-01-01T12:30:00Z",
            observation_method="verified_publication_timestamp",
        )


@pytest.mark.parametrize(
    "value",
    [
        "2026-01-01T12:30:00",
        "invalid",
        "",
        None,
        10,
        "2999-01-01T00:00:00Z",
    ],
)
def test_http_adapter_rejects_invalid_provider_observation(value):
    result = HttpRetrievalProvider(TEMPLATE)._normalize_payload(
        {
            "sources": [
                {
                    "uri": URI_A,
                    "content": "One.",
                    "observed_at": value,
                }
            ]
        },
        TEMPLATE.replace("{query}", "current"),
    )
    assert result.status == "failed"
    assert result.reason == "invalid_source_observed_at"
    assert result.sources == ()
    assert result.content is None


def test_http_adapter_carries_explicit_source_timestamps():
    result = HttpRetrievalProvider(TEMPLATE)._normalize_payload(
        {"sources": [{
            "uri": URI_A,
            "content": "Observed.",
            "observed_at": "2026-01-01T18:00:00+05:30",
        }]},
        TEMPLATE.replace("{query}", "current"),
    )
    assert result.status == "completed"
    assert result.sources[0]["observed_at"] == "2026-01-01T12:30:00Z"


@pytest.mark.parametrize(
    "value",
    ["2026-01-01T12:30:00", "not-time", None, 10,
     "2999-01-01T00:00:00Z"],
)
def test_provider_neutral_evidence_rejects_invalid_time(value):
    result = RetrievalEvidenceNormalizer().normalize_result({
        "status": "completed",
        "sources": [{
            "uri": URI_A,
            "content": "Observed.",
            "observed_at": value,
        }],
        "content": "Observed.",
    })
    assert result.status == "invalid_evidence"
    assert result.has_content is False


def test_provider_neutral_evidence_retains_valid_timestamp():
    result = RetrievalEvidenceNormalizer().normalize_result({
        "status": "completed",
        "sources": [{
            "uri": URI_A,
            "content": "Observed.",
            "observed_at": "2026-01-01T18:00:00+05:30",
        }],
        "content": None,
    })
    assert result.status == "completed"
    assert result.sources[0]["observed_at"] == "2026-01-01T12:30:00Z"


@pytest.mark.parametrize(
    "value",
    [0, -1, True, False, "3600", "0", float("nan"),
     float("inf"), float("-inf"), 10**1000],
)
def test_api_rejects_invalid_or_nonfinite_freshness_windows(value):
    with pytest.raises(ValueError, match="freshness_max_age_seconds"):
        RealityStateRequest(
            task="Current status?",
            freshness_max_age_seconds=value,
        )


def test_api_default_retains_task_only_invocation():
    request = RealityStateRequest(task="Current status?")
    assert request.freshness_max_age_seconds is None


def test_api_passes_declared_window_to_retrieval_builder(monkeypatch):
    captured = {}

    def fake_build(task, freshness_max_age_seconds=None):
        captured["task"] = task
        captured["max_age"] = freshness_max_age_seconds
        return {"status": "uncertain"}

    monkeypatch.setattr("backend.app.main.build_reality_state", fake_build)
    reality_state(RealityStateRequest(
        task="What is the current status?",
        freshness_max_age_seconds=3600,
    ))
    assert captured == {
        "task": "What is the current status?",
        "max_age": 3600,
    }


def test_api_openapi_exposes_optional_retrieval_policy():
    schema = app.openapi()["components"]["schemas"]["RealityStateRequest"]
    assert "freshness_max_age_seconds" in schema["properties"]
    assert "freshness_max_age_seconds" not in schema.get("required", [])
    assert "documents" not in schema["properties"]


def test_domain_boundary_rejects_invalid_window_before_retrieval():
    for bad in (0, -1, True, "3600", float("nan"), float("inf"), 10**1000):
        with pytest.raises(ValueError, match="positive finite"):
            build_reality_state(
                "What is the current status?",
                dependencies=_deps(),
                freshness_max_age_seconds=bad,
            )


def test_builder_preserves_mixed_observation_provenance_without_window():
    sources = _sources(partial=True)
    builder = SourceObservationBuilder(clock=lambda: NOW)
    provenance = SourceProvenanceBuilder().build_result({
        "status": "completed",
        "content": "A. B.",
        "sources": sources,
    })
    result = builder.build_retrieval_result(provenance, sources)
    assert result.status == "usable"
    assert [item.observation_method for item in result.observations] == [
        "retrieval_provider_observation",
        "retrieval_observation",
    ]
    assert [item.observed_at for item in result.observations] == [
        "2026-01-01T12:30:00Z",
        "2026-01-01T13:00:00Z",
    ]


def test_builder_requires_each_explicit_time_when_policy_declared():
    sources = _sources(partial=True)
    provenance = SourceProvenanceBuilder().build_result({
        "status": "completed",
        "content": "A. B.",
        "sources": sources,
    })
    result = SourceObservationBuilder(clock=lambda: NOW).build_retrieval_result(
        provenance,
        sources,
        require_provider_observations=True,
    )
    assert result.status == "unavailable"
    assert result.reason == "provider_observation_required"
    assert result.observations == ()


def test_builder_rejects_mismatched_provider_sources():
    sources = _sources()
    provenance = SourceProvenanceBuilder().build_result({
        "status": "completed",
        "content": "A. B.",
        "sources": sources,
    })
    result = SourceObservationBuilder(clock=lambda: NOW).build_retrieval_result(
        provenance, [sources[0]], require_provider_observations=True,
    )
    assert result.status == "unavailable"
    assert result.reason == "retrieval_source_provenance_mismatch"


def test_retrieved_sources_all_fresh_produce_structural_support(monkeypatch):
    state = _build(monkeypatch, _sources())
    assert state["evidence"]["status"] == "completed"
    assert state["claims"]["status"] == "usable"
    assert state["claim_evidence_linking"]["linked_claim_count"] == 2
    observations = state["source_observation"]["observations"]
    assert len(observations) == 2
    assert {o["observation_method"] for o in observations} == {
        "retrieval_provider_observation",
    }
    assert {o["observed_at"] for o in observations} == {
        "2026-01-01T12:30:00Z",
        "2026-01-01T12:45:00Z",
    }
    assert state["freshness"]["fresh_count"] == 2
    assert state["freshness"]["stale_count"] == 0
    assert state["freshness"]["unknown_count"] == 0
    assert state["confidence_signals"]["status"] == "supported"
    assert state["status"] == "supported"


def test_retrieved_sources_stale_remain_uncertain(monkeypatch):
    state = _build(monkeypatch, _sources(older=True))
    assert state["freshness"]["fresh_count"] == 1
    assert state["freshness"]["stale_count"] == 1
    assert state["freshness"]["unknown_count"] == 0
    assert state["status"] == "uncertain"
    assert "stale_sources_present" in state["confidence_signals"]["signals"]


def test_requested_window_without_provider_times_is_never_fresh(monkeypatch):
    state = _build(monkeypatch, _sources(partial=True))
    assert state["claims"]["status"] == "usable"
    assert state["source_provenance"]["status"] == "usable"
    assert state["source_observation"]["status"] == "unavailable"
    assert state["source_observation"]["reason"] == (
        "provider_observation_required"
    )
    assert state["freshness"]["status"] == "unavailable"
    assert state["freshness"]["fresh_count"] == 0
    assert state["status"] != "supported"


def test_window_with_only_legacy_sources_is_not_fresh(monkeypatch):
    sources = [{"uri": URI_A, "content": "Company X launched Feature A."}]
    state = _build(monkeypatch, sources)
    assert state["source_observation"]["status"] == "unavailable"
    assert state["freshness"]["status"] == "unavailable"
    assert state["status"] != "supported"


def test_provider_reported_time_without_declared_policy_remains_unknown(
    monkeypatch,
):
    state = _build(monkeypatch, _sources(), max_age=None)
    assert state["source_observation"]["status"] == "usable"
    assert {o["observation_method"] for o in
            state["source_observation"]["observations"]} == {
        "retrieval_provider_observation"
    }
    assert state["freshness"]["unknown_count"] == 2
    assert state["status"] == "uncertain"


def test_legacy_retrieval_without_policy_retains_observation_semantics(
    monkeypatch,
):
    _fake_http(
        monkeypatch,
        {"sources": [{"uri": URI_A, "content": "Legacy evidence."}]},
    )
    state = build_reality_state(
        "What is the current status?",
        dependencies=_deps(),
    )
    assert state["source_observation"]["status"] == "usable"
    assert state["source_observation"]["observations"][0][
        "observation_method"
    ] == "retrieval_observation"
    assert state["freshness"]["unknown_count"] == 1
    assert state["status"] == "uncertain"
