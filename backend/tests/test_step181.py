from dataclasses import replace
from datetime import datetime, timezone

import pytest

from backend.app.api.evidence_reality_state import (
    EvidenceRealityStateRequest,
)
from backend.app.main import app, reality_state_from_evidence
from backend.app.orchestrator.dependencies import OrchestrationDependencies
from backend.app.orchestrator.orchestrator import build_reality_state_from_evidence
from backend.app.reality.source_freshness_evaluator import (
    SourceFreshnessEvaluator,
)
from backend.app.reality.source_observation import SourceObservation
from backend.app.reality.submitted_evidence import SubmittedEvidenceBundle


NOW = datetime(2026, 1, 1, 3, 0, tzinfo=timezone.utc)


def _dependencies():
    return replace(
        OrchestrationDependencies.default(),
        source_freshness_evaluator=SourceFreshnessEvaluator(
            clock=lambda: NOW
        ),
    )


def _fresh_documents():
    return [
        {
            "title": "Source A",
            "uri": "https://example.test/a",
            "content": "Company X launched Feature A.",
            "observed_at": "2026-01-01T02:30:00Z",
        },
        {
            "title": "Source B",
            "uri": "https://example.test/b",
            "content": "Company X continues to operate.",
            "observed_at": "2026-01-01T02:15:00+00:00",
        },
    ]


def _mixed_freshness_documents():
    documents = _fresh_documents()
    documents[1]["observed_at"] = "2026-01-01T00:00:00Z"
    return documents


def test_request_accepts_explicit_observation_time_and_freshness_window():
    request = EvidenceRealityStateRequest(
        task="What is the current status of Company X?",
        documents=_fresh_documents(),
        freshness_max_age_seconds=3600,
    )

    assert request.freshness_max_age_seconds == 3600
    assert request.documents[0].observed_at == "2026-01-01T02:30:00Z"
    assert request.documents[1].observed_at == "2026-01-01T02:15:00Z"


def test_request_rejects_invalid_observation_timestamps():
    naive = _fresh_documents()
    naive[0]["observed_at"] = "2026-01-01T02:30:00"
    with pytest.raises(Exception, match="timezone"):
        EvidenceRealityStateRequest(
            task="task",
            documents=naive,
        )

    future = _fresh_documents()
    future[0]["observed_at"] = "2999-01-01T00:00:00Z"
    with pytest.raises(Exception, match="future"):
        EvidenceRealityStateRequest(
            task="task",
            documents=future,
        )

    malformed = _fresh_documents()
    malformed[0]["observed_at"] = "not-a-timestamp"
    with pytest.raises(Exception, match="ISO-8601"):
        EvidenceRealityStateRequest(
            task="task",
            documents=malformed,
        )


@pytest.mark.parametrize(
    "value",
    [0, -1, True, "3600"],
)
def test_request_rejects_invalid_freshness_window(value):
    with pytest.raises(
        Exception,
        match="freshness_max_age_seconds must be a positive number",
    ):
        EvidenceRealityStateRequest(
            task="task",
            documents=_fresh_documents(),
            freshness_max_age_seconds=value,
        )


def test_freshness_window_requires_observed_at_for_every_document():
    documents = _fresh_documents()
    documents[1].pop("observed_at")

    with pytest.raises(
        Exception,
        match="requires observed_at for every document",
    ):
        EvidenceRealityStateRequest(
            task="task",
            documents=documents,
            freshness_max_age_seconds=3600,
        )


def test_domain_boundary_also_requires_observed_at_when_window_declared():
    documents = _fresh_documents()
    documents[0].pop("observed_at")

    with pytest.raises(
        ValueError,
        match="requires observed_at for every document",
    ):
        build_reality_state_from_evidence(
            "task",
            documents,
            freshness_max_age_seconds=3600,
            dependencies=_dependencies(),
        )


def test_submitted_source_observation_methods_are_canonical():
    explicit = SourceObservation(
        "source-1",
        "2026-01-01T00:00:00Z",
        "submitted_evidence_observation",
    )
    ingestion = SourceObservation(
        "source-2",
        "2026-01-01T00:00:00Z",
        "submitted_evidence_ingestion",
    )

    assert explicit.observation_method == "submitted_evidence_observation"
    assert ingestion.observation_method == "submitted_evidence_ingestion"

    with pytest.raises(ValueError, match="observation_method"):
        SourceObservation(
            "source-3",
            "2026-01-01T00:00:00Z",
            "caller_asserted_truth",
        )


def test_bundle_uses_explicit_observation_time_when_supplied():
    bundle = SubmittedEvidenceBundle.from_mappings(_fresh_documents())
    services = _dependencies()
    evidence = bundle.to_evidence()
    provenance = services.source_provenance_builder.build_result(evidence)

    observations = bundle.build_observations(
        provenance,
        clock=lambda: NOW,
    )

    assert observations.status == "usable"
    assert observations.source_count == 2
    assert {
        item.observation_method
        for item in observations.observations
    } == {"submitted_evidence_observation"}
    assert observations.observations[0].observed_at == (
        "2026-01-01T02:30:00Z"
    )


def test_bundle_marks_missing_observation_time_as_ingestion_not_retrieval():
    documents = _fresh_documents()
    for document in documents:
        document.pop("observed_at")

    bundle = SubmittedEvidenceBundle.from_mappings(documents)
    services = _dependencies()
    provenance = services.source_provenance_builder.build_result(
        bundle.to_evidence()
    )

    observations = bundle.build_observations(
        provenance,
        clock=lambda: NOW,
    )

    assert {
        item.observation_method
        for item in observations.observations
    } == {"submitted_evidence_ingestion"}
    assert {
        item.observed_at
        for item in observations.observations
    } == {"2026-01-01T03:00:00Z"}


def test_all_sources_within_declared_window_can_be_supported():
    state = build_reality_state_from_evidence(
        "What is the current status of Company X?",
        _fresh_documents(),
        freshness_max_age_seconds=3600,
        dependencies=_dependencies(),
    )

    freshness = state["freshness"]
    assert freshness["fresh_count"] == 2
    assert freshness["stale_count"] == 0
    assert freshness["unknown_count"] == 0
    assert {
        item["status"]
        for item in freshness["assessments"]
    } == {"fresh"}

    observation = state["source_observation"]
    assert {
        item["observation_method"]
        for item in observation["observations"]
    } == {"submitted_evidence_observation"}

    confidence = state["confidence_signals"]
    assert confidence["status"] == "supported"
    assert "sources_within_declared_observation_window" in (
        confidence["signals"]
    )


def test_one_stale_source_keeps_reality_state_uncertain():
    state = build_reality_state_from_evidence(
        "What is the current status of Company X?",
        _mixed_freshness_documents(),
        freshness_max_age_seconds=3600,
        dependencies=_dependencies(),
    )

    freshness = state["freshness"]
    assert freshness["fresh_count"] == 1
    assert freshness["stale_count"] == 1
    assert freshness["unknown_count"] == 0

    confidence = state["confidence_signals"]
    assert confidence["status"] == "uncertain"
    assert "stale_sources_present" in confidence["signals"]


def test_observed_at_without_window_remains_unknown_freshness():
    state = build_reality_state_from_evidence(
        "What is the current status of Company X?",
        _fresh_documents(),
        dependencies=_dependencies(),
    )

    freshness = state["freshness"]
    assert freshness["unknown_count"] == 2
    assert freshness["fresh_count"] == 0
    assert freshness["stale_count"] == 0
    assert {
        item["reason"]
        for item in freshness["assessments"]
    } == {"freshness_window_not_declared"}

    assert state["confidence_signals"]["status"] == "uncertain"


def test_http_handler_passes_explicit_freshness_policy(monkeypatch):
    request = EvidenceRealityStateRequest(
        task="What is the current status of Company X?",
        documents=_fresh_documents(),
        freshness_max_age_seconds=3600,
    )

    captured = {}

    def fake_build(task, documents, freshness_max_age_seconds=None):
        captured["task"] = task
        captured["documents"] = documents
        captured["freshness_max_age_seconds"] = freshness_max_age_seconds
        return {
            "status": "uncertain",
            "task": task,
            "evidence": {},
            "claims": {},
            "claim_evidence_linking": {},
            "source_provenance": {},
            "source_observation": {},
            "freshness": {},
            "conflicts": {},
            "confidence_signals": {},
            "assembly_method": "deterministic_signal_snapshot",
            "reason": None,
        }

    monkeypatch.setattr(
        "backend.app.main.build_reality_state_from_evidence",
        fake_build,
    )

    reality_state_from_evidence(request)

    assert captured["freshness_max_age_seconds"] == 3600
    assert captured["documents"][0]["observed_at"] == (
        "2026-01-01T02:30:00Z"
    )


def test_openapi_documents_freshness_input_fields():
    schema = app.openapi()
    request_schema = schema["components"]["schemas"][
        "EvidenceRealityStateRequest"
    ]
    document_schema = schema["components"]["schemas"][
        "EvidenceDocumentInput"
    ]

    assert "freshness_max_age_seconds" in request_schema["properties"]
    assert "observed_at" in document_schema["properties"]
