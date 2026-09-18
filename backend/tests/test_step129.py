from datetime import datetime, timezone

import pytest

from backend.app.reality.source_freshness import SourceFreshnessAssessment, SourceFreshnessResult
from backend.app.reality.source_freshness_evaluator import SourceFreshnessEvaluator
from backend.app.reality.source_observation import SourceObservation, SourceObservationResult


def observations():
    return SourceObservationResult.usable_result((SourceObservation("id-1", "2026-09-18T12:00:00Z"),))


def clock():
    return datetime(2026, 9, 18, 13, 0, tzinfo=timezone.utc)


def test_fresh_assessment_uses_explicit_window():
    result = SourceFreshnessEvaluator(clock=clock).evaluate_result(observations(), max_age_seconds=3600)
    assert result.status == "usable"
    assert result.fresh_count == 1
    assert result.stale_count == 0
    assert result.assessments[0].age_seconds == 3600


def test_stale_assessment_uses_explicit_window():
    result = SourceFreshnessEvaluator(clock=clock).evaluate_result(observations(), max_age_seconds=3599)
    assert result.stale_count == 1
    assert result.assessments[0].status == "stale"


def test_missing_window_is_unknown_not_fresh():
    result = SourceFreshnessEvaluator(clock=clock).evaluate_result(observations())
    assert result.unknown_count == 1
    assert result.assessments[0].reason == "freshness_window_not_declared"


def test_unavailable_and_empty_observations_propagate():
    evaluator = SourceFreshnessEvaluator(clock=clock)
    assert evaluator.evaluate_result(SourceObservationResult.unavailable_result("no_observation")).status == "unavailable"
    assert evaluator.evaluate_result(SourceObservationResult.empty_result()).status == "empty"


def test_invalid_window_and_clock_fail_closed():
    with pytest.raises(ValueError, match="positive number"):
        SourceFreshnessEvaluator(clock=clock).evaluate_result(observations(), max_age_seconds=0)
    with pytest.raises(ValueError, match="timezone-aware"):
        SourceFreshnessEvaluator(clock=lambda: datetime(2026, 9, 18, 13, 0)).evaluate_result(observations(), max_age_seconds=3600)


def test_result_contract_counts_and_immutability():
    item = SourceFreshnessAssessment("id-1", "unknown", "2026-09-18T12:00:00Z", reason="missing")
    result = SourceFreshnessResult.usable_result((item,))
    assert result.to_dict()["unknown_count"] == 1
    with pytest.raises(Exception):
        item.source_id = "changed"
    with pytest.raises(ValueError, match="fresh or stale assessment requires"):
        SourceFreshnessAssessment("id-1", "fresh", "2026-09-18T12:00:00Z")
