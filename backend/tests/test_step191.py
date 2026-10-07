"""Step 191 — canonical unknown-freshness policy integrity."""

from datetime import datetime, timezone

import pytest

from backend.app.reality.confidence_signal_aggregator import (
    RealityConfidenceSignalAggregator,
)
from backend.app.reality.source_freshness import (
    SourceFreshnessAssessment,
    SourceFreshnessResult,
)
from backend.app.reality.source_freshness_evaluator import SourceFreshnessEvaluator
from backend.app.reality.source_freshness_normalizer import (
    SourceFreshnessResultNormalizer,
)
from backend.app.reality.source_observation import (
    SourceObservation,
    SourceObservationResult,
)


OBSERVED = "2026-01-01T12:00:00Z"
NOW = datetime(2026, 1, 1, 12, 30, tzinfo=timezone.utc)


def _unknown_mapping(
    *,
    age_seconds: float | None = None,
    max_age_seconds: float | None = None,
    reason: str = "freshness_window_not_declared",
) -> dict:
    return {
        "status": "usable",
        "assessments": [
            {
                "source_id": "source-1",
                "status": "unknown",
                "observed_at": OBSERVED,
                "age_seconds": age_seconds,
                "max_age_seconds": max_age_seconds,
                "assessment_method": "observation_age",
                "reason": reason,
            }
        ],
        "source_count": 1,
        "fresh_count": 0,
        "stale_count": 0,
        "unknown_count": 1,
        "freshness_executed": True,
        "reason": None,
    }


def _observations() -> SourceObservationResult:
    return SourceObservationResult.usable_result(
        (SourceObservation("source-1", OBSERVED),)
    )


def test_unknown_assessment_rejects_declared_freshness_window():
    with pytest.raises(
        ValueError,
        match="unknown assessment requires max_age_seconds to be None",
    ):
        SourceFreshnessAssessment(
            source_id="source-1",
            status="unknown",
            observed_at=OBSERVED,
            max_age_seconds=3600,
            reason="freshness_window_not_declared",
        )


def test_unknown_assessment_rejects_window_even_with_measured_age():
    with pytest.raises(
        ValueError,
        match="unknown assessment requires max_age_seconds to be None",
    ):
        SourceFreshnessAssessment(
            source_id="source-1",
            status="unknown",
            observed_at=OBSERVED,
            age_seconds=1800,
            max_age_seconds=3600,
            reason="freshness_window_not_declared",
        )


def test_unknown_mapping_rejects_declared_freshness_window():
    with pytest.raises(
        ValueError,
        match="unknown assessment requires max_age_seconds to be None",
    ):
        SourceFreshnessResult.validate(
            _unknown_mapping(max_age_seconds=3600)
        )


def test_unknown_normalizer_rejects_declared_freshness_window():
    with pytest.raises(
        ValueError,
        match="unknown assessment requires max_age_seconds to be None",
    ):
        SourceFreshnessResultNormalizer.normalize(
            _unknown_mapping(
                age_seconds=1800,
                max_age_seconds=3600,
            )
        )


def test_unknown_without_window_remains_valid():
    assessment = SourceFreshnessAssessment(
        source_id="source-1",
        status="unknown",
        observed_at=OBSERVED,
        reason="freshness_window_not_declared",
    )

    assert assessment.status == "unknown"
    assert assessment.max_age_seconds is None
    assert assessment.age_seconds is None


def test_unknown_may_preserve_finite_observation_age_without_policy_window():
    assessment = SourceFreshnessAssessment(
        source_id="source-1",
        status="unknown",
        observed_at=OBSERVED,
        age_seconds=1800,
        reason="freshness_window_not_declared",
    )

    assert assessment.status == "unknown"
    assert assessment.age_seconds == 1800
    assert assessment.max_age_seconds is None


def test_unknown_mapping_with_age_but_no_window_remains_valid():
    result = SourceFreshnessResultNormalizer.normalize(
        _unknown_mapping(age_seconds=1800)
    )

    assert result.unknown_count == 1
    assert result.assessments[0].age_seconds == 1800
    assert result.assessments[0].max_age_seconds is None


def test_unknown_still_requires_a_reason():
    with pytest.raises(ValueError, match="unknown assessment requires a reason"):
        SourceFreshnessAssessment(
            source_id="source-1",
            status="unknown",
            observed_at=OBSERVED,
        )


def test_evaluator_without_window_produces_unknown_without_policy_measurement():
    result = SourceFreshnessEvaluator(clock=lambda: NOW).evaluate_result(
        _observations()
    )

    assert result.status == "usable"
    assert result.unknown_count == 1
    assert result.fresh_count == 0
    assert result.stale_count == 0
    assessment = result.assessments[0]
    assert assessment.status == "unknown"
    assert assessment.max_age_seconds is None
    assert assessment.reason == "freshness_window_not_declared"


def test_evaluator_with_declared_window_produces_classified_not_unknown():
    result = SourceFreshnessEvaluator(clock=lambda: NOW).evaluate_result(
        _observations(),
        max_age_seconds=3600,
    )

    assert result.status == "usable"
    assert result.fresh_count == 1
    assert result.stale_count == 0
    assert result.unknown_count == 0
    assert result.assessments[0].max_age_seconds == 3600.0


def test_unknown_freshness_still_makes_confidence_uncertain():
    freshness = SourceFreshnessResult.usable_result(
        (
            SourceFreshnessAssessment(
                source_id="source-1",
                status="unknown",
                observed_at=OBSERVED,
                reason="freshness_window_not_declared",
            ),
        )
    ).to_dict()

    result = RealityConfidenceSignalAggregator().aggregate_result(
        evidence_quality={"status": "usable"},
        linking={
            "status": "usable",
            "claim_count": 1,
            "linked_claim_count": 1,
        },
        freshness=freshness,
        conflicts={"status": "empty", "conflict_count": 0},
    )

    assert result.status == "uncertain"
    assert "freshness_uncertain" in result.signals


def test_step190_fresh_and_stale_classification_rules_remain_intact():
    fresh = SourceFreshnessAssessment(
        source_id="source-1",
        status="fresh",
        observed_at=OBSERVED,
        age_seconds=60,
        max_age_seconds=60,
    )
    stale = SourceFreshnessAssessment(
        source_id="source-2",
        status="stale",
        observed_at=OBSERVED,
        age_seconds=61,
        max_age_seconds=60,
    )

    assert fresh.status == "fresh"
    assert stale.status == "stale"


def test_step186_finite_age_rule_still_applies_to_unknown():
    with pytest.raises(ValueError, match="age_seconds"):
        SourceFreshnessAssessment(
            source_id="source-1",
            status="unknown",
            observed_at=OBSERVED,
            age_seconds=float("inf"),
            reason="freshness_window_not_declared",
        )


def test_step189_timestamp_rule_still_applies_to_unknown():
    with pytest.raises(ValueError):
        SourceFreshnessAssessment(
            source_id="source-1",
            status="unknown",
            observed_at="2026-01-01T12:00:00",
            reason="freshness_window_not_declared",
        )
