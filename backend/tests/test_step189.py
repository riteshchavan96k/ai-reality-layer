"""Step 189 — canonical observation/freshness timestamp integrity."""

from datetime import datetime, timezone

import pytest

from backend.app.orchestrator.orchestrator import build_reality_state_from_evidence
from backend.app.reality.source_freshness import (
    SourceFreshnessAssessment,
    SourceFreshnessResult,
)
from backend.app.reality.source_freshness_evaluator import SourceFreshnessEvaluator
from backend.app.reality.source_freshness_normalizer import (
    SourceFreshnessResultNormalizer,
)
from backend.app.reality.source_observation import (
    MAX_SOURCE_OBSERVED_AT_CHARS,
    SourceObservation,
    SourceObservationResult,
)
from backend.app.reality.source_observation_normalizer import (
    SourceObservationResultNormalizer,
)


OBSERVED = "2026-01-01T12:30:00Z"
OFFSET = "2026-01-01T18:00:00+05:30"
FUTURE = "2999-01-01T00:00:00Z"
URI = "https://example.test/source"


def _exact_length_timestamp() -> str:
    return OBSERVED + " " * (MAX_SOURCE_OBSERVED_AT_CHARS - len(OBSERVED))


def _observation_mapping(observed_at: object) -> dict:
    return {
        "status": "usable",
        "observations": [
            {
                "source_id": "source-1",
                "observed_at": observed_at,
                "observation_method": "retrieval_provider_observation",
            }
        ],
        "source_count": 1,
        "observation_executed": True,
        "reason": None,
    }


def _freshness_mapping(observed_at: object) -> dict:
    return {
        "status": "usable",
        "assessments": [
            {
                "source_id": "source-1",
                "status": "fresh",
                "observed_at": observed_at,
                "age_seconds": 1800.0,
                "max_age_seconds": 3600.0,
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


def test_typed_source_observation_canonicalizes_utc_offset():
    observation = SourceObservation(
        "source-1",
        OFFSET,
        "retrieval_provider_observation",
    )

    assert observation.observed_at == OBSERVED
    assert observation.to_dict()["observed_at"] == OBSERVED


def test_source_observation_result_mapping_canonicalizes_timestamp():
    result = SourceObservationResultNormalizer.normalize(
        _observation_mapping(OFFSET)
    )

    assert result.observations[0].observed_at == OBSERVED
    assert result.to_dict()["observations"][0]["observed_at"] == OBSERVED


def test_typed_source_observation_accepts_exact_raw_boundary_and_normalizes():
    raw = _exact_length_timestamp()
    assert len(raw) == MAX_SOURCE_OBSERVED_AT_CHARS

    observation = SourceObservation("source-1", raw)

    assert observation.observed_at == OBSERVED


@pytest.mark.parametrize("size", [65, 128, 100_000])
def test_typed_source_observation_rejects_overlong_raw_timestamp(size):
    raw = OBSERVED + " " * (size - len(OBSERVED))

    with pytest.raises(ValueError, match="exceeds 64"):
        SourceObservation("source-1", raw)


@pytest.mark.parametrize(
    "bad",
    [
        "2026-01-01T12:30:00",
        "not-a-time",
        "",
        " ",
        None,
        123,
        FUTURE,
    ],
)
def test_typed_source_observation_rejects_noncanonical_invalid_values(bad):
    with pytest.raises(ValueError):
        SourceObservation("source-1", bad)  # type: ignore[arg-type]


def test_direct_freshness_assessment_canonicalizes_utc_offset():
    assessment = SourceFreshnessAssessment(
        source_id="source-1",
        status="fresh",
        observed_at=OFFSET,
        age_seconds=1800,
        max_age_seconds=3600,
    )

    assert assessment.observed_at == OBSERVED
    assert assessment.to_dict()["observed_at"] == OBSERVED


def test_freshness_result_mapping_canonicalizes_timestamp():
    result = SourceFreshnessResultNormalizer.normalize(
        _freshness_mapping(OFFSET)
    )

    assert result.assessments[0].observed_at == OBSERVED
    assert result.to_dict()["assessments"][0]["observed_at"] == OBSERVED


def test_freshness_assessment_accepts_exact_raw_boundary_and_normalizes():
    raw = _exact_length_timestamp()
    assert len(raw) == MAX_SOURCE_OBSERVED_AT_CHARS

    assessment = SourceFreshnessAssessment(
        source_id="source-1",
        status="fresh",
        observed_at=raw,
        age_seconds=1800,
        max_age_seconds=3600,
    )

    assert assessment.observed_at == OBSERVED


@pytest.mark.parametrize("size", [65, 128, 100_000])
def test_freshness_assessment_rejects_overlong_raw_timestamp(size):
    raw = OBSERVED + " " * (size - len(OBSERVED))

    with pytest.raises(ValueError, match="exceeds 64"):
        SourceFreshnessAssessment(
            source_id="source-1",
            status="fresh",
            observed_at=raw,
            age_seconds=1800,
            max_age_seconds=3600,
        )


@pytest.mark.parametrize(
    "bad",
    [
        "2026-01-01T12:30:00",
        "not-a-time",
        "",
        " ",
        None,
        123,
        FUTURE,
    ],
)
def test_freshness_assessment_rejects_invalid_observation_timestamp(bad):
    with pytest.raises(ValueError):
        SourceFreshnessAssessment(
            source_id="source-1",
            status="fresh",
            observed_at=bad,  # type: ignore[arg-type]
            age_seconds=1800,
            max_age_seconds=3600,
        )


def test_freshness_mapping_rejects_invalid_timestamp_before_canonical_result():
    raw = OBSERVED + " " * (MAX_SOURCE_OBSERVED_AT_CHARS + 1 - len(OBSERVED))

    with pytest.raises(ValueError, match="exceeds 64"):
        SourceFreshnessResult.validate(_freshness_mapping(raw))


def test_unknown_freshness_keeps_semantics_while_canonicalizing_timestamp():
    assessment = SourceFreshnessAssessment(
        source_id="source-1",
        status="unknown",
        observed_at=OFFSET,
        reason="freshness_window_not_declared",
    )
    result = SourceFreshnessResult.usable_result((assessment,))

    assert result.unknown_count == 1
    assert result.fresh_count == 0
    assert result.stale_count == 0
    assert result.assessments[0].observed_at == OBSERVED


def test_freshness_evaluator_keeps_age_policy_and_canonical_timestamp():
    now = datetime(2026, 1, 1, 13, 0, tzinfo=timezone.utc)
    observations = SourceObservationResult.usable_result(
        (
            SourceObservation(
                "source-1",
                OFFSET,
                "retrieval_provider_observation",
            ),
        )
    )

    result = SourceFreshnessEvaluator(clock=lambda: now).evaluate_result(
        observations,
        max_age_seconds=3600,
    )

    assert result.status == "usable"
    assert result.fresh_count == 1
    assert result.stale_count == 0
    assert result.assessments[0].age_seconds == 1800
    assert result.assessments[0].observed_at == OBSERVED


def test_submitted_evidence_reality_state_keeps_one_canonical_timestamp():
    state = build_reality_state_from_evidence(
        "What is the current status of Company X?",
        [
            {
                "uri": URI,
                "content": "Company X is operational.",
                "observed_at": OFFSET,
            }
        ],
    )

    assert state["source_observation"]["observations"][0]["observed_at"] == OBSERVED
    assert state["freshness"]["assessments"][0]["observed_at"] == OBSERVED
    assert state["freshness"]["unknown_count"] == 1
    assert state["claims"]["claim_count"] == 1
    assert state["claims"]["claims"][0]["source_refs"] == [URI]


def test_step188_shared_limit_remains_the_canonical_timestamp_limit():
    assert MAX_SOURCE_OBSERVED_AT_CHARS == 64
