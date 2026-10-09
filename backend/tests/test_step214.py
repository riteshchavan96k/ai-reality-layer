"""Step 214 — unique temporal source identities for observations and freshness.

Provenance records are unique after Step 213. Direct typed and mapping-shaped
observation/freshness results must not double count a source downstream.
"""

from datetime import datetime, timezone

import pytest

from backend.app.orchestrator.orchestrator import build_reality_state_from_evidence
from backend.app.reality.source_freshness import (
    SourceFreshnessAssessment,
    SourceFreshnessResult,
)
from backend.app.reality.source_freshness_evaluator import SourceFreshnessEvaluator
from backend.app.reality.source_freshness_normalizer import SourceFreshnessResultNormalizer
from backend.app.reality.source_observation import (
    SourceObservation,
    SourceObservationResult,
)
from backend.app.reality.source_observation_builder import SourceObservationBuilder
from backend.app.reality.source_observation_normalizer import (
    SourceObservationResultNormalizer,
)
from backend.app.reality.source_provenance import (
    SourceProvenance,
    SourceProvenanceResult,
)

A = "https://example.test/source-a"
B = "https://example.test/source-b"
OBSERVED = "2026-01-01T12:00:00Z"
NOW = datetime(2026, 1, 1, 12, 30, tzinfo=timezone.utc)


def _observation(source_id="id-a", method="retrieval_provider_observation"):
    return SourceObservation(
        source_id=source_id,
        observed_at=OBSERVED,
        observation_method=method,
    )


def _unknown(source_id="id-a"):
    return SourceFreshnessAssessment(
        source_id=source_id, status="unknown",
        observed_at=OBSERVED, reason="freshness_window_not_declared",
    )


def _fresh(source_id="id-a"):
    return SourceFreshnessAssessment(
        source_id=source_id, status="fresh",
        observed_at=OBSERVED, age_seconds=1800, max_age_seconds=3600,
    )


def _stale(source_id="id-a"):
    return SourceFreshnessAssessment(
        source_id=source_id, status="stale",
        observed_at=OBSERVED, age_seconds=1800, max_age_seconds=1200,
    )


@pytest.mark.parametrize("observations", [
    (_observation(), _observation()),
    (_observation(), _observation(method="submitted_evidence_observation")),
])
def test_typed_observation_rejects_duplicate_source_even_if_method_differs(
    observations,
):
    with pytest.raises(ValueError, match="source observation source_ids must be unique"):
        SourceObservationResult.usable_result(observations)


def test_typed_observation_rejects_duplicate_ids_in_explicit_constructor():
    with pytest.raises(ValueError, match="source observation source_ids must be unique"):
        SourceObservationResult(
            status="usable",
            observations=(_observation(), _observation()),
            source_count=2,
        )


@pytest.mark.parametrize("mapping_style", ["dicts", "typed"])
def test_observation_mapping_and_normalizer_reject_duplicate_ids(mapping_style):
    records = [_observation(), _observation(method="submitted_evidence_observation")]
    result = {
        "status": "usable",
        "observations": (
            [x.to_dict() for x in records] if mapping_style == "dicts" else records
        ),
        "source_count": 2,
        "observation_executed": True,
        "reason": None,
    }
    with pytest.raises(ValueError, match="source observation source_ids must be unique"):
        SourceObservationResult.validate(result)
    with pytest.raises(ValueError, match="source observation source_ids must be unique"):
        SourceObservationResultNormalizer.normalize(result)


@pytest.mark.parametrize("assessments", [
    (_fresh(), _fresh()),
    (_fresh(), _stale()),
    (_unknown(), _fresh()),
])
def test_typed_freshness_rejects_duplicate_ids_and_conflicting_states(assessments):
    with pytest.raises(ValueError, match="source freshness source_ids must be unique"):
        SourceFreshnessResult.usable_result(assessments)


def test_explicit_freshness_constructor_rejects_duplicates_despite_valid_counts():
    with pytest.raises(ValueError, match="source freshness source_ids must be unique"):
        SourceFreshnessResult(
            status="usable",
            assessments=(_fresh(), _stale()),
            source_count=2,
            fresh_count=1,
            stale_count=1,
            unknown_count=0,
        )


@pytest.mark.parametrize("as_typed", [False, True])
def test_mapping_and_normalizer_reject_duplicate_freshness_assessments(as_typed):
    assessments = (_fresh(), _stale())
    raw = {
        "status": "usable",
        "assessments": (
            list(assessments) if as_typed else [item.to_dict() for item in assessments]
        ),
        "source_count": 2,
        "fresh_count": 1,
        "stale_count": 1,
        "unknown_count": 0,
        "freshness_executed": True,
        "reason": None,
    }
    with pytest.raises(ValueError, match="source freshness source_ids must be unique"):
        SourceFreshnessResult.validate(raw)
    with pytest.raises(ValueError, match="source freshness source_ids must be unique"):
        SourceFreshnessResultNormalizer.normalize(raw)


def test_freshness_evaluator_rejects_duplicate_observations_before_counting():
    raw = {
        "status": "usable",
        "observations": [
            _observation().to_dict(),
            _observation(method="submitted_evidence_observation").to_dict(),
        ],
        "source_count": 2,
        "observation_executed": True,
        "reason": None,
    }
    with pytest.raises(ValueError, match="source observation source_ids must be unique"):
        SourceFreshnessEvaluator(clock=lambda: NOW).evaluate_result(
            raw, max_age_seconds=3600
        )


def test_distinct_observations_roundtrip_and_freshness_evaluation():
    observations = SourceObservationResult.usable_result(
        (_observation("id-a"), _observation("id-b"))
    )
    assert observations.source_count == 2
    assert SourceObservationResult.validate(observations.to_dict()) == observations
    assert SourceObservationResultNormalizer.normalize(observations.to_dict()) == observations

    freshness = SourceFreshnessEvaluator(clock=lambda: NOW).evaluate_result(
        observations, max_age_seconds=3600
    )
    assert freshness.status == "usable"
    assert freshness.source_count == freshness.fresh_count == 2
    assert [item.source_id for item in freshness.assessments] == ["id-a", "id-b"]
    assert SourceFreshnessResult.validate(freshness.to_dict()) == freshness
    assert SourceFreshnessResultNormalizer.normalize(freshness.to_dict()) == freshness


def test_mixed_distinct_freshness_statuses_keep_exact_aggregates():
    result = SourceFreshnessResult.usable_result(
        (_fresh("id-a"), _stale("id-b"), _unknown("id-c"))
    )
    assert (result.source_count, result.fresh_count, result.stale_count, result.unknown_count) == (3, 1, 1, 1)
    assert SourceFreshnessResult.validate(result.to_dict()) == result


def test_provenance_builder_to_observation_to_freshness_keeps_one_source_each():
    provenance = SourceProvenanceResult.usable_result((
        SourceProvenance("id-a", A, A),
        SourceProvenance("id-b", B, B),
    ))
    observations = SourceObservationBuilder(clock=lambda: NOW).build_retrieval_result(
        provenance,
        [
            {"uri": A, "observed_at": OBSERVED},
            {"uri": B, "observed_at": OBSERVED},
        ],
        require_provider_observations=True,
    )
    assert observations.status == "usable"
    assert observations.source_count == 2
    assert {item.source_id for item in observations.observations} == {"id-a", "id-b"}
    freshness = SourceFreshnessEvaluator(clock=lambda: NOW).evaluate_result(
        observations, max_age_seconds=3600
    )
    assert freshness.fresh_count == 2
    assert freshness.source_count == 2


def test_historical_empty_unavailable_and_unknown_semantics_unchanged():
    assert SourceObservationResult.empty_result().source_count == 0
    assert SourceObservationResult.unavailable_result("no_sources").status == "unavailable"
    assert SourceFreshnessResult.empty_result().fresh_count == 0
    assert SourceFreshnessResult.unavailable_result("not_available").status == "unavailable"
    unknown = SourceFreshnessResult.usable_result((_unknown(),))
    assert unknown.source_count == unknown.unknown_count == 1


def test_end_to_end_reality_state_does_not_double_count_observed_sources():
    state = build_reality_state_from_evidence(
        "What is the evidence about Company X?",
        [
            {"uri": A, "content": "Company X announced Feature A."},
            {"uri": B, "content": "Company X announced Feature A."},
        ],
        entity="Company X",
    )
    provenance = state["source_provenance"]
    observations = state["source_observation"]
    freshness = state["freshness"]
    assert provenance["status"] == observations["status"] == "usable"
    assert len({record["source_id"] for record in provenance["sources"]}) == 2
    assert len({record["source_id"] for record in observations["observations"]}) == 2
    assert provenance["source_count"] == observations["source_count"] == 2
    assert freshness["status"] == "usable"
    assert freshness["source_count"] == freshness["unknown_count"] == 2
    assert len({record["source_id"] for record in freshness["assessments"]}) == 2
    assert state["claims"]["claims"][0]["source_refs"] == [A, B]
