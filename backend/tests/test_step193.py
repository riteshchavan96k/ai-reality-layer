"""Step 193 — canonical freshness execution-state integrity."""

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


def _fresh_assessment() -> SourceFreshnessAssessment:
    return SourceFreshnessAssessment(
        source_id="source-1",
        status="fresh",
        observed_at=OBSERVED,
        age_seconds=1800,
        max_age_seconds=3600,
    )


def _usable_mapping(*, freshness_executed: object) -> dict:
    return {
        "status": "usable",
        "assessments": [_fresh_assessment().to_dict()],
        "source_count": 1,
        "fresh_count": 1,
        "stale_count": 0,
        "unknown_count": 0,
        "freshness_executed": freshness_executed,
        "reason": None,
    }


def test_usable_result_rejects_false_execution_flag():
    with pytest.raises(
        ValueError,
        match="usable freshness result requires freshness_executed to be True",
    ):
        SourceFreshnessResult(
            status="usable",
            assessments=(_fresh_assessment(),),
            source_count=1,
            fresh_count=1,
            stale_count=0,
            unknown_count=0,
            freshness_executed=False,
        )


def test_mapping_rejects_usable_false_execution_flag():
    with pytest.raises(
        ValueError,
        match="usable freshness result requires freshness_executed to be True",
    ):
        SourceFreshnessResult.validate(
            _usable_mapping(freshness_executed=False)
        )


def test_normalizer_rejects_usable_false_execution_flag():
    with pytest.raises(
        ValueError,
        match="usable freshness result requires freshness_executed to be True",
    ):
        SourceFreshnessResultNormalizer.normalize(
            _usable_mapping(freshness_executed=False)
        )


def test_usable_true_execution_flag_remains_valid():
    result = SourceFreshnessResult.validate(
        _usable_mapping(freshness_executed=True)
    )

    assert result.status == "usable"
    assert result.freshness_executed is True
    assert result.fresh_count == 1


def test_non_boolean_execution_flag_remains_rejected():
    raw = _usable_mapping(freshness_executed=1)

    with pytest.raises(
        ValueError,
        match="freshness_executed must be a boolean",
    ):
        SourceFreshnessResult.validate(raw)


def test_empty_result_may_explicitly_record_not_executed():
    result = SourceFreshnessResult(
        status="empty",
        freshness_executed=False,
    )

    assert result.status == "empty"
    assert result.freshness_executed is False
    assert result.source_count == 0


def test_unavailable_result_may_explicitly_record_not_executed():
    result = SourceFreshnessResult(
        status="unavailable",
        freshness_executed=False,
        reason="freshness_not_executed",
    )

    assert result.status == "unavailable"
    assert result.freshness_executed is False
    assert result.reason == "freshness_not_executed"


def test_existing_empty_helper_remains_executed_true():
    result = SourceFreshnessResult.empty_result()

    assert result.status == "empty"
    assert result.freshness_executed is True


def test_existing_unavailable_helper_remains_executed_true():
    result = SourceFreshnessResult.unavailable_result(
        "source_observation_unavailable"
    )

    assert result.status == "unavailable"
    assert result.freshness_executed is True


def test_evaluator_usable_result_records_execution_true():
    observations = SourceObservationResult.usable_result(
        (SourceObservation("source-1", OBSERVED),)
    )

    result = SourceFreshnessEvaluator(clock=lambda: NOW).evaluate_result(
        observations,
        max_age_seconds=3600,
    )

    assert result.status == "usable"
    assert result.freshness_executed is True
    assert result.fresh_count == 1


def test_evaluator_unknown_result_still_records_execution_true():
    observations = SourceObservationResult.usable_result(
        (SourceObservation("source-1", OBSERVED),)
    )

    result = SourceFreshnessEvaluator(clock=lambda: NOW).evaluate_result(
        observations
    )

    assert result.status == "usable"
    assert result.freshness_executed is True
    assert result.unknown_count == 1


def test_evaluator_empty_result_keeps_existing_execution_semantics():
    result = SourceFreshnessEvaluator(clock=lambda: NOW).evaluate_result(
        SourceObservationResult.empty_result()
    )

    assert result.status == "empty"
    assert result.freshness_executed is True


def test_evaluator_unavailable_result_keeps_existing_execution_semantics():
    result = SourceFreshnessEvaluator(clock=lambda: NOW).evaluate_result(
        SourceObservationResult.unavailable_result(
            "source_observation_unavailable"
        )
    )

    assert result.status == "unavailable"
    assert result.freshness_executed is True


def test_valid_executed_freshness_remains_compatible_with_confidence():
    freshness = SourceFreshnessResult.usable_result(
        (_fresh_assessment(),)
    ).to_dict()

    confidence = RealityConfidenceSignalAggregator().aggregate_result(
        evidence_quality={"status": "usable"},
        linking={
            "status": "usable",
            "claim_count": 1,
            "linked_claim_count": 1,
        },
        freshness=freshness,
        conflicts={"status": "empty", "conflict_count": 0},
    )

    assert freshness["freshness_executed"] is True
    assert confidence.status == "supported"
    assert "sources_within_declared_observation_window" in confidence.signals


def test_step192_strict_count_integrity_remains_intact():
    with pytest.raises(
        ValueError,
        match="fresh_count must be a non-negative integer",
    ):
        SourceFreshnessResult(
            status="usable",
            assessments=(_fresh_assessment(),),
            source_count=1,
            fresh_count=True,
            stale_count=0,
            unknown_count=0,
        )


def test_step191_unknown_policy_integrity_remains_intact():
    with pytest.raises(
        ValueError,
        match="unknown assessment requires max_age_seconds to be None",
    ):
        SourceFreshnessAssessment(
            source_id="source-1",
            status="unknown",
            observed_at=OBSERVED,
            max_age_seconds=60,
            reason="freshness_window_not_declared",
        )
