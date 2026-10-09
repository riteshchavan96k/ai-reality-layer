"""Step 219: prevent confident Reality States with explicitly wrong entities.

The new gate is conservative *text* alignment only, not semantic entailment
or authentication of submitted URL content. Benchmarks must remain honest.
"""

from dataclasses import replace
from datetime import datetime, timezone

import pytest

from backend.app.api.evidence_reality_state import EvidenceRealityStateRequest
from backend.app.api.reality_state import RealityStateResponse
from backend.app.main import reality_state_from_evidence
from backend.app.orchestrator.dependencies import OrchestrationDependencies
from backend.app.orchestrator.orchestrator import (
    build_reality_state, build_reality_state_from_evidence,
)
from backend.app.reality.confidence_signal_aggregator import RealityConfidenceSignalAggregator
from backend.app.reality.entity_relevance import explicit_entity_link_alignment
from backend.app.reality.reality_entity import RealityEntity
from backend.app.reality.reality_state_builder import RealityStateBuilder
from backend.app.reality.retrieval_result import RetrievalResultContract
from backend.app.reality.source_freshness_evaluator import SourceFreshnessEvaluator


NOW = datetime(2026, 1, 1, 13, 0, tzinfo=timezone.utc)
OBSERVED = "2026-01-01T12:30:00Z"
URI = "https://example.test/release"
TARGET = "Python 3.13.0"
CORRECT = "Python 3.13.0 was released on October 7, 2024."
WRONG = "Python 3.12.0 was released on October 2, 2023."


def _links(*claims):
    return {
        "status": "usable",
        "claim_count": len(claims),
        "linked_claim_count": len(claims),
        "links": [
            {"claim_text": text, "source_ref": URI}
            for text in claims
        ],
    }


def _confidence(*claims, entity=TARGET):
    return RealityConfidenceSignalAggregator().aggregate_result(
        {"status": "usable"},
        _links(*claims),
        {"status": "usable", "stale_count": 0, "unknown_count": 0},
        {"status": "empty", "conflict_count": 0},
        entity=entity,
    )


def _deps():
    return replace(
        OrchestrationDependencies.default(),
        source_freshness_evaluator=SourceFreshnessEvaluator(clock=lambda: NOW),
        reality_state_builder=RealityStateBuilder(clock=lambda: NOW),
    )


def _state(text, entity=TARGET):
    return build_reality_state_from_evidence(
        f"What was the release date of {TARGET}?",
        [{"uri": URI, "content": text, "observed_at": OBSERVED}],
        freshness_max_age_seconds=3600,
        entity=entity,
        dependencies=_deps(),
    )


def test_full_explicit_entity_match_retains_structural_support():
    result = _confidence(CORRECT)
    assert result.status == "supported"
    assert result.claim_coverage == 1.0
    assert "explicit_entity_text_alignment_only" in result.signals


def test_wrong_version_reduces_confidence_without_changing_source_coverage():
    result = _confidence(WRONG)
    assert result.status == "uncertain"
    assert result.claim_coverage == 1.0
    assert result.freshness_status == "usable"
    assert result.conflict_count == 0
    assert "explicit_entity_not_aligned_with_all_linked_claims" in result.signals
    assert "claims_have_evidence_links" in result.signals
    assert "sources_within_declared_observation_window" in result.signals


@pytest.mark.parametrize(
    "entity,claim",
    [
        ("Go 1.24", "Go 1.24.0 is available."),
        ("Python 3.13", "Python 3.13.0 was released."),
        ("Python 3.13.0", "Python 3.13.0-rc1 is available."),
        ("Node.js 24", "Node.js 240 was released."),
        ("Company X", "Company XYZ shipped the product."),
        ("Alpha-Beta", "Alpha-Beta2 was updated."),
        ("Cedar Search", "A Cedar Searching plugin was installed."),
        ("ABC", "XABC was announced."),
    ],
)
def test_partial_identifiers_are_not_entity_alignment(entity, claim):
    assert explicit_entity_link_alignment(entity, _links(claim)) is False


@pytest.mark.parametrize(
    "entity,claim",
    [
        ("Python 3.13.0", "PYTHON 3.13.0 was released."),
        ("Company X", "COMPANY X announced an update."),
        ("Node.js 24.0.0", "Node.js 24.0.0 (released) is ready."),
        ("Cedar Search", "The Cedar Search platform works."),
        ("Alpha-Beta", "The Alpha-Beta service is enabled."),
        ("Go 1.24", "Go 1.24: release notes."),
    ],
)
def test_casefold_and_identifier_boundaries_allow_valid_names(entity, claim):
    assert explicit_entity_link_alignment(entity, _links(claim)) is True


def test_whitespace_normalization_does_not_change_name_identity():
    assert explicit_entity_link_alignment(
        RealityEntity.specified("  Company   X  "),
        _links("Company X announced the release."),
    )
    assert explicit_entity_link_alignment(
        "Company X", _links("Company\tX announced the release.")
    )


def test_each_link_must_match_not_just_one_arbitrary_link():
    assert explicit_entity_link_alignment(TARGET, _links(CORRECT, WRONG)) is False
    result = _confidence(CORRECT, WRONG)
    assert result.status == "uncertain"


@pytest.mark.parametrize(
    "bad_links",
    [
        {},
        {"status": "empty", "links": []},
        {"status": "usable", "links": []},
        {"status": "usable", "links": None},
        {"status": "usable", "links": [None]},
        {"status": "usable", "links": [{"source_ref": URI}]},
        {"status": "usable", "links": [{"claim_text": 42}]},
    ],
)
def test_missing_or_malformed_links_cannot_count_as_relevance(bad_links):
    assert explicit_entity_link_alignment(TARGET, bad_links) is False


def test_unspecified_entity_is_not_eligible_for_an_alignment_claim():
    with pytest.raises(ValueError, match="explicitly specified"):
        explicit_entity_link_alignment(RealityEntity.unspecified(), _links(CORRECT))


def test_legacy_confidence_without_entity_remains_unchanged():
    result = _confidence(WRONG, entity=None)
    assert result.status == "supported"
    assert not any("explicit_entity" in value for value in result.signals)


def test_explicit_entity_as_mapping_has_same_safety_gate():
    result = _confidence(WRONG, entity=RealityEntity.specified(TARGET).to_dict())
    assert result.status == "uncertain"


def test_submitted_evidence_wrong_topic_is_uncertain_end_to_end():
    state = _state(WRONG)
    assert state["status"] == "uncertain"
    assert state["confidence_signals"]["status"] == "uncertain"
    assert state["confidence_signals"]["claim_coverage"] == 1.0
    assert state["freshness"]["fresh_count"] == 1
    assert state["conflicts"]["conflict_count"] == 0
    assert state["entity"]["name"] == TARGET
    assert "explicit_entity_not_aligned_with_all_linked_claims" in (
        state["confidence_signals"]["signals"]
    )
    RealityStateResponse.model_validate(state)


def test_submitted_evidence_on_topic_remains_structurally_supported():
    state = _state(CORRECT)
    assert state["status"] == "supported"
    assert "explicit_entity_text_alignment_only" in state["confidence_signals"]["signals"]
    assert state["claim_evidence_linking"]["linked_claim_count"] == 1


def test_submitted_evidence_no_explicit_entity_keeps_legacy_support():
    state = _state(WRONG, entity=None)
    assert state["status"] == "supported"
    assert state["entity"]["status"] == "unspecified"


def test_target_entity_mention_does_not_authenticate_forged_content():
    state = _state("Not " + CORRECT)
    # This safeguard cannot know whether the submitted URL truly says this.
    assert state["status"] == "supported"
    assert "explicit_entity_text_alignment_only" in state["confidence_signals"]["signals"]


def test_existing_api_handler_uses_explicit_entity_alignment():
    request = EvidenceRealityStateRequest.model_validate({
        "task": "What date did Python 3.13.0 ship?",
        "entity": TARGET,
        "documents": [{"uri": URI, "content": WRONG}],
    })
    response = reality_state_from_evidence(request)
    assert response["status"] == "uncertain"
    assert response["confidence_signals"]["status"] == "uncertain"


class _CompletedEngine:
    def __init__(self, content):
        self.content = content

    def retrieve(self, contract):
        return RetrievalResultContract.completed(
            contract["request"],
            provider="test-provider",
            sources=[{
                "title": "Test release",
                "uri": URI,
                "content": self.content,
                "observed_at": OBSERVED,
            }],
            content=self.content,
        )


def test_retrieved_evidence_uses_same_explicit_entity_alignment():
    state = build_reality_state(
        f"What is the current status of {TARGET}?",
        retrieval_engine=_CompletedEngine(WRONG),
        freshness_max_age_seconds=3600,
        entity=TARGET,
        dependencies=_deps(),
    )
    assert state["evidence"]["status"] == "completed"
    assert state["status"] == "uncertain"
    assert "explicit_entity_not_aligned_with_all_linked_claims" in (
        state["confidence_signals"]["signals"]
    )


def test_retrieved_evidence_valid_entity_retains_structural_support():
    state = build_reality_state(
        f"What is the current status of {TARGET}?",
        retrieval_engine=_CompletedEngine(CORRECT),
        freshness_max_age_seconds=3600,
        entity=TARGET,
        dependencies=_deps(),
    )
    assert state["evidence"]["status"] == "completed"
    assert state["status"] == "supported"


def test_entity_alignment_is_not_factual_truth_verification():
    unrelated_false_report = "Python 3.13.0 was released on January 1, 2000."
    assert explicit_entity_link_alignment(TARGET, _links(unrelated_false_report))
    assert _confidence(unrelated_false_report).status == "supported"
