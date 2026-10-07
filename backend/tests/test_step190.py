"""Step 190 — canonical freshness classification consistency."""

from datetime import datetime, timedelta, timezone

import pytest

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


def _mapping(
    *,
    status: str,
    age_seconds: float,
    max_age_seconds: float,
) -> dict:
    return {
        "status": "usable",
        "assessments": [
            {
                "source_id": "source-1",
                "status": status,
                "observed_at": OBSERVED,
                "age_seconds": age_seconds,
                "max_age_seconds": max_age_seconds,
                "assessment_method": "observation_age",
                "reason": None,
            }
        ],
        "source_count": 1,
        "fresh_count": 1 if status == "fresh" else 0,
        "stale_count": 1 if status == "stale" else 0,
        "unknown_count": 0,
        "freshness_executed": True,
        "reason": None,
    }


def test_fresh_assessment_rejects_age_beyond_declared_window():
    with pytest.raises(
        ValueError,
        match="fresh assessment requires age_seconds <= max_age_seconds",
    ):
        SourceFreshnessAssessment(
            source_id="source-1",
            status="fresh",
            observed_at=OBSERVED,
            age_seconds=61,
            max_age_seconds=60,
        )


def test_stale_assessment_rejects_age_inside_declared_window():
    with pytest.raises(
        ValueError,
        match="stale assessment requires age_seconds > max_age_seconds",
    ):
        SourceFreshnessAssessment(
            source_id="source-1",
            status="stale",
            observed_at=OBSERVED,
            age_seconds=59,
            max_age_seconds=60,
        )


def test_stale_assessment_rejects_exact_window_boundary():
    with pytest.raises(
        ValueError,
        match="stale assessment requires age_seconds > max_age_seconds",
    ):
        SourceFreshnessAssessment(
            source_id="source-1",
            status="stale",
            observed_at=OBSERVED,
            age_seconds=60,
            max_age_seconds=60,
        )


def test_fresh_assessment_accepts_exact_window_boundary():
    assessment = SourceFreshnessAssessment(
        source_id="source-1",
        status="fresh",
        observed_at=OBSERVED,
        age_seconds=60,
        max_age_seconds=60,
    )

    assert assessment.status == "fresh"
    assert assessment.age_seconds == 60
    assert assessment.max_age_seconds == 60


def test_stale_assessment_accepts_age_strictly_beyond_window():
    assessment = SourceFreshnessAssessment(
        source_id="source-1",
        status="stale",
        observed_at=OBSERVED,
        age_seconds=60.000001,
        max_age_seconds=60,
    )

    assert assessment.status == "stale"


def test_mapping_rejects_contradictory_fresh_classification():
    with pytest.raises(
        ValueError,
        match="fresh assessment requires age_seconds <= max_age_seconds",
    ):
        SourceFreshnessResult.validate(
            _mapping(
                status="fresh",
                age_seconds=3601,
                max_age_seconds=3600,
            )
        )


def test_mapping_rejects_contradictory_stale_classification():
    with pytest.raises(
        ValueError,
        match="stale assessment requires age_seconds > max_age_seconds",
    ):
        SourceFreshnessResultNormalizer.normalize(
            _mapping(
                status="stale",
                age_seconds=3599,
                max_age_seconds=3600,
            )
        )


def test_mapping_accepts_consistent_fresh_classification():
    result = SourceFreshnessResultNormalizer.normalize(
        _mapping(
            status="fresh",
            age_seconds=3600,
            max_age_seconds=3600,
        )
    )

    assert result.fresh_count == 1
    assert result.stale_count == 0
    assert result.assessments[0].status == "fresh"


def test_mapping_accepts_consistent_stale_classification():
    result = SourceFreshnessResultNormalizer.normalize(
        _mapping(
            status="stale",
            age_seconds=3600.1,
            max_age_seconds=3600,
        )
    )

    assert result.fresh_count == 0
    assert result.stale_count == 1
    assert result.assessments[0].status == "stale"


def test_unknown_assessment_semantics_remain_reason_based():
    assessment = SourceFreshnessAssessment(
        source_id="source-1",
        status="unknown",
        observed_at=OBSERVED,
        reason="freshness_window_not_declared",
    )

    assert assessment.status == "unknown"
    assert assessment.age_seconds is None
    assert assessment.max_age_seconds is None


def test_evaluator_classifies_exact_window_boundary_as_fresh():
    observed = datetime(2026, 1, 1, 12, 0, tzinfo=timezone.utc)
    observations = SourceObservationResult.usable_result(
        (SourceObservation("source-1", OBSERVED),)
    )
    result = SourceFreshnessEvaluator(
        clock=lambda: observed + timedelta(seconds=60)
    ).evaluate_result(
        observations,
        max_age_seconds=60,
    )

    assert result.fresh_count == 1
    assert result.stale_count == 0
    assert result.assessments[0].age_seconds == 60
    assert result.assessments[0].max_age_seconds == 60.0


def test_evaluator_classifies_just_over_window_as_stale():
    observed = datetime(2026, 1, 1, 12, 0, tzinfo=timezone.utc)
    observations = SourceObservationResult.usable_result(
        (SourceObservation("source-1", OBSERVED),)
    )
    result = SourceFreshnessEvaluator(
        clock=lambda: observed + timedelta(seconds=61)
    ).evaluate_result(
        observations,
        max_age_seconds=60,
    )

    assert result.fresh_count == 0
    assert result.stale_count == 1
    assert result.assessments[0].age_seconds == 61


def test_step186_finite_numeric_contract_remains_required():
    with pytest.raises(ValueError):
        SourceFreshnessAssessment(
            source_id="source-1",
            status="fresh",
            observed_at=OBSERVED,
            age_seconds=float("inf"),
            max_age_seconds=60,
        )


def test_step189_timestamp_contract_remains_required():
    with pytest.raises(ValueError):
        SourceFreshnessAssessment(
            source_id="source-1",
            status="fresh",
            observed_at="2026-01-01T12:00:00",
            age_seconds=1,
            max_age_seconds=60,
        )
