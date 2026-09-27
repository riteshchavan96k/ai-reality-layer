from datetime import datetime, timezone

import pytest

from backend.app.reality.source_freshness import SourceFreshnessAssessment, SourceFreshnessResult
from backend.app.reality.source_freshness_evaluator import SourceFreshnessEvaluator
from backend.app.reality.source_freshness_normalizer import SourceFreshnessResultNormalizer
from backend.app.reality.source_observation import SourceObservation, SourceObservationResult


def test_step159_accepts_canonical_freshness_result():
    assessment = SourceFreshnessAssessment(
        source_id="source-1",
        status="fresh",
        observed_at="2026-01-01T00:00:00Z",
        age_seconds=10,
        max_age_seconds=60,
    )
    result = SourceFreshnessResult.usable_result((assessment,))

    assert SourceFreshnessResult.validate(result) is result


def test_step159_normalizes_mapping():
    result = SourceFreshnessResultNormalizer.normalize(
        {
            "status": "usable",
            "assessments": [
                {
                    "source_id": "source-1",
                    "status": "fresh",
                    "observed_at": "2026-01-01T00:00:00Z",
                    "age_seconds": 10,
                    "max_age_seconds": 60,
                    "assessment_method": "observation_age",
                    "reason": None,
                }
            ],
            "source_count": 1,
            "fresh_count": 1,
            "stale_count": 0,
            "unknown_count": 0,
            "freshness_executed": True,
            "reason": None,
        }
    )

    assert result.status == "usable"
    assert result.source_count == 1
    assert result.fresh_count == 1


def test_step159_rejects_missing_required_result_field():
    with pytest.raises(ValueError, match="missing required fields"):
        SourceFreshnessResult.validate(
            {
                "status": "usable",
                "assessments": [],
                "source_count": 0,
            }
        )


def test_step159_rejects_assessment_count_mismatch():
    with pytest.raises(ValueError, match="source_count must match"):
        SourceFreshnessResultNormalizer.normalize(
            {
                "status": "empty",
                "assessments": [],
                "source_count": 1,
                "fresh_count": 0,
                "stale_count": 0,
                "unknown_count": 0,
                "freshness_executed": True,
                "reason": None,
            }
        )


def test_step159_rejects_inconsistent_freshness_counts():
    with pytest.raises(ValueError, match="freshness counts must match"):
        SourceFreshnessResultNormalizer.normalize(
            {
                "status": "usable",
                "assessments": [
                    {
                        "source_id": "source-1",
                        "status": "fresh",
                        "observed_at": "2026-01-01T00:00:00Z",
                        "age_seconds": 10,
                        "max_age_seconds": 60,
                        "assessment_method": "observation_age",
                        "reason": None,
                    }
                ],
                "source_count": 1,
                "fresh_count": 0,
                "stale_count": 1,
                "unknown_count": 0,
                "freshness_executed": True,
                "reason": None,
            }
        )


def test_step159_evaluator_returns_canonical_validated_result():
    now = datetime(2026, 1, 1, 0, 1, tzinfo=timezone.utc)
    observation = SourceObservation("source-1", "2026-01-01T00:00:00Z")
    observations = SourceObservationResult.usable_result((observation,))

    result = SourceFreshnessEvaluator(clock=lambda: now).evaluate_result(
        observations,
        max_age_seconds=120,
    )

    assert isinstance(result, SourceFreshnessResult)
    assert result.status == "usable"
    assert result.fresh_count == 1
    assert result.stale_count == 0
    assert result.unknown_count == 0


def test_step159_preserves_unknown_when_window_is_not_declared():
    now = datetime(2026, 1, 1, 0, 1, tzinfo=timezone.utc)
    observation = SourceObservation("source-1", "2026-01-01T00:00:00Z")
    observations = SourceObservationResult.usable_result((observation,))

    result = SourceFreshnessEvaluator(clock=lambda: now).evaluate_result(observations)

    assert result.status == "usable"
    assert result.unknown_count == 1
    assert result.assessments[0].reason == "freshness_window_not_declared"
