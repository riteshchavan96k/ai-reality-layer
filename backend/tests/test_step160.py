import pytest

from backend.app.reality.confidence_signal_aggregator import RealityConfidenceSignalAggregator
from backend.app.reality.confidence_signal_normalizer import RealityConfidenceSignalResultNormalizer
from backend.app.reality.confidence_signals import RealityConfidenceSignalResult


def test_step160_accepts_canonical_confidence_result():
    result = RealityConfidenceSignalResult(
        status="supported",
        evidence_usable=True,
        claim_coverage=1.0,
        freshness_status="usable",
        conflict_count=0,
        signals=("claims_have_evidence_links", "sources_within_declared_observation_window"),
    )
    assert RealityConfidenceSignalResult.validate(result) is result


def test_step160_normalizes_mapping():
    result = RealityConfidenceSignalResultNormalizer.normalize(
        {
            "status": "uncertain",
            "evidence_usable": True,
            "claim_coverage": 0.5,
            "freshness_status": "usable",
            "conflict_count": 0,
            "signals": ["partial_claim_evidence_coverage"],
            "confidence_method": "deterministic_signal_aggregation",
            "reason": None,
        }
    )
    assert result.status == "uncertain"
    assert result.claim_coverage == 0.5


def test_step160_rejects_missing_required_result_field():
    with pytest.raises(ValueError, match="missing required fields"):
        RealityConfidenceSignalResult.validate(
            {
                "status": "supported",
                "evidence_usable": True,
                "claim_coverage": 1.0,
                "freshness_status": "usable",
            }
        )


def test_step160_rejects_invalid_claim_coverage():
    with pytest.raises(ValueError, match="claim_coverage"):
        RealityConfidenceSignalResultNormalizer.normalize(
            {
                "status": "uncertain",
                "evidence_usable": True,
                "claim_coverage": 1.5,
                "freshness_status": "usable",
                "conflict_count": 0,
                "signals": [],
                "confidence_method": "deterministic_signal_aggregation",
                "reason": None,
            }
        )


def test_step160_rejects_invalid_conflict_count():
    with pytest.raises(ValueError, match="conflict_count"):
        RealityConfidenceSignalResultNormalizer.normalize(
            {
                "status": "uncertain",
                "evidence_usable": True,
                "claim_coverage": 1.0,
                "freshness_status": "usable",
                "conflict_count": -1,
                "signals": [],
                "confidence_method": "deterministic_signal_aggregation",
                "reason": None,
            }
        )


def test_step160_aggregator_returns_canonical_validated_result():
    result = RealityConfidenceSignalAggregator().aggregate_result(
        evidence_quality={"status": "usable"},
        linking={"status": "usable", "claim_count": 2, "linked_claim_count": 2},
        freshness={"status": "usable", "stale_count": 0, "unknown_count": 0},
        conflicts={"status": "empty", "conflict_count": 0},
    )
    assert isinstance(result, RealityConfidenceSignalResult)
    assert result.status == "supported"
    assert result.claim_coverage == 1.0


def test_step160_preserves_uncertainty_for_partial_grounding():
    result = RealityConfidenceSignalAggregator().aggregate_result(
        evidence_quality={"status": "usable"},
        linking={"status": "usable", "claim_count": 2, "linked_claim_count": 1},
        freshness={"status": "usable", "stale_count": 0, "unknown_count": 0},
        conflicts={"status": "empty", "conflict_count": 0},
    )
    assert result.status == "uncertain"
    assert "partial_claim_evidence_coverage" in result.signals
