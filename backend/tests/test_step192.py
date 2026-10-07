"""Step 192 — canonical freshness count type integrity."""

import pytest

from backend.app.reality.confidence_signal_aggregator import (
    RealityConfidenceSignalAggregator,
)
from backend.app.reality.source_freshness import (
    SourceFreshnessAssessment,
    SourceFreshnessResult,
)
from backend.app.reality.source_freshness_normalizer import (
    SourceFreshnessResultNormalizer,
)


OBSERVED = "2026-01-01T12:00:00Z"


def _fresh_assessment() -> SourceFreshnessAssessment:
    return SourceFreshnessAssessment(
        source_id="source-fresh",
        status="fresh",
        observed_at=OBSERVED,
        age_seconds=60,
        max_age_seconds=60,
    )


def _stale_assessment() -> SourceFreshnessAssessment:
    return SourceFreshnessAssessment(
        source_id="source-stale",
        status="stale",
        observed_at=OBSERVED,
        age_seconds=61,
        max_age_seconds=60,
    )


def _unknown_assessment() -> SourceFreshnessAssessment:
    return SourceFreshnessAssessment(
        source_id="source-unknown",
        status="unknown",
        observed_at=OBSERVED,
        reason="freshness_window_not_declared",
    )


def _mapping(
    assessments: list[dict],
    *,
    source_count: object,
    fresh_count: object,
    stale_count: object,
    unknown_count: object,
) -> dict:
    return {
        "status": "usable",
        "assessments": assessments,
        "source_count": source_count,
        "fresh_count": fresh_count,
        "stale_count": stale_count,
        "unknown_count": unknown_count,
        "freshness_executed": True,
        "reason": None,
    }


def _fresh_mapping() -> dict:
    return _fresh_assessment().to_dict()


def test_source_count_rejects_boolean_even_when_true_equals_one():
    with pytest.raises(
        ValueError,
        match="source_count must be a non-negative integer",
    ):
        SourceFreshnessResult(
            status="usable",
            assessments=(_fresh_assessment(),),
            source_count=True,
            fresh_count=1,
            stale_count=0,
            unknown_count=0,
        )


@pytest.mark.parametrize("value", [1.0, "1", None])
def test_source_count_rejects_non_integer_types(value):
    with pytest.raises(
        ValueError,
        match="source_count must be a non-negative integer",
    ):
        SourceFreshnessResult(
            status="usable",
            assessments=(_fresh_assessment(),),
            source_count=value,  # type: ignore[arg-type]
            fresh_count=1,
            stale_count=0,
            unknown_count=0,
        )


@pytest.mark.parametrize(
    ("field", "value", "expected_message"),
    [
        ("fresh_count", True, "fresh_count must be a non-negative integer"),
        ("fresh_count", 1.0, "fresh_count must be a non-negative integer"),
        ("fresh_count", "1", "fresh_count must be a non-negative integer"),
        ("stale_count", False, "stale_count must be a non-negative integer"),
        ("stale_count", 0.0, "stale_count must be a non-negative integer"),
        ("stale_count", "0", "stale_count must be a non-negative integer"),
        ("unknown_count", False, "unknown_count must be a non-negative integer"),
        ("unknown_count", 0.0, "unknown_count must be a non-negative integer"),
        ("unknown_count", "0", "unknown_count must be a non-negative integer"),
    ],
)
def test_aggregate_counts_reject_bool_float_and_string(
    field,
    value,
    expected_message,
):
    kwargs = {
        "status": "usable",
        "assessments": (_fresh_assessment(),),
        "source_count": 1,
        "fresh_count": 1,
        "stale_count": 0,
        "unknown_count": 0,
    }
    kwargs[field] = value

    with pytest.raises(ValueError, match=expected_message):
        SourceFreshnessResult(**kwargs)


@pytest.mark.parametrize(
    ("field", "value"),
    [
        ("fresh_count", -1),
        ("stale_count", -1),
        ("unknown_count", -1),
    ],
)
def test_aggregate_counts_reject_negative_integers(field, value):
    kwargs = {
        "status": "usable",
        "assessments": (_fresh_assessment(),),
        "source_count": 1,
        "fresh_count": 1,
        "stale_count": 0,
        "unknown_count": 0,
    }
    kwargs[field] = value

    with pytest.raises(ValueError, match=f"{field} must be a non-negative integer"):
        SourceFreshnessResult(**kwargs)


def test_mapping_rejects_boolean_source_count():
    raw = _mapping(
        [_fresh_mapping()],
        source_count=True,
        fresh_count=1,
        stale_count=0,
        unknown_count=0,
    )

    with pytest.raises(
        ValueError,
        match="source_count must be a non-negative integer",
    ):
        SourceFreshnessResult.validate(raw)


def test_mapping_rejects_float_count_that_compares_equal_to_integer():
    raw = _mapping(
        [_fresh_mapping()],
        source_count=1,
        fresh_count=1.0,
        stale_count=0,
        unknown_count=0,
    )

    with pytest.raises(
        ValueError,
        match="fresh_count must be a non-negative integer",
    ):
        SourceFreshnessResultNormalizer.normalize(raw)


def test_mapping_rejects_false_zero_count_that_compares_equal_to_zero():
    raw = _mapping(
        [_fresh_mapping()],
        source_count=1,
        fresh_count=1,
        stale_count=False,
        unknown_count=0,
    )

    with pytest.raises(
        ValueError,
        match="stale_count must be a non-negative integer",
    ):
        SourceFreshnessResultNormalizer.normalize(raw)


def test_valid_integer_counts_remain_accepted_for_mixed_assessments():
    result = SourceFreshnessResult.usable_result(
        (
            _fresh_assessment(),
            _stale_assessment(),
            _unknown_assessment(),
        )
    )

    assert result.source_count == 3
    assert result.fresh_count == 1
    assert result.stale_count == 1
    assert result.unknown_count == 1
    for value in (
        result.source_count,
        result.fresh_count,
        result.stale_count,
        result.unknown_count,
    ):
        assert type(value) is int


def test_empty_result_keeps_zero_integer_counts():
    result = SourceFreshnessResult.empty_result()

    assert result.status == "empty"
    assert result.source_count == 0
    assert result.fresh_count == 0
    assert result.stale_count == 0
    assert result.unknown_count == 0
    assert all(
        type(value) is int
        for value in (
            result.source_count,
            result.fresh_count,
            result.stale_count,
            result.unknown_count,
        )
    )


def test_unavailable_result_keeps_zero_integer_counts():
    result = SourceFreshnessResult.unavailable_result(
        "source_observation_unavailable"
    )

    assert result.status == "unavailable"
    assert result.source_count == 0
    assert result.fresh_count == 0
    assert result.stale_count == 0
    assert result.unknown_count == 0


def test_step190_classification_integrity_remains_intact():
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


def test_strict_integer_counts_remain_compatible_with_confidence_aggregation():
    freshness = SourceFreshnessResult.usable_result(
        (_fresh_assessment(),)
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

    assert result.status == "supported"
    assert "sources_within_declared_observation_window" in result.signals
