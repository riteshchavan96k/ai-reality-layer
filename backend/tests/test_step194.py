"""Step 194 — canonical source-observation execution-state integrity."""

from datetime import datetime, timezone

import pytest

from backend.app.reality.source_freshness_evaluator import SourceFreshnessEvaluator
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


OBSERVED = "2026-01-01T12:00:00Z"
NOW = datetime(2026, 1, 1, 12, 30, tzinfo=timezone.utc)


def _observation() -> SourceObservation:
    return SourceObservation(
        source_id="source-1",
        observed_at=OBSERVED,
        observation_method="retrieval_provider_observation",
    )


def _usable_mapping(*, observation_executed: object) -> dict:
    return {
        "status": "usable",
        "observations": [_observation().to_dict()],
        "source_count": 1,
        "observation_executed": observation_executed,
        "reason": None,
    }


def test_usable_result_rejects_false_execution_flag():
    with pytest.raises(
        ValueError,
        match="usable source observation requires observation_executed to be True",
    ):
        SourceObservationResult(
            status="usable",
            observations=(_observation(),),
            source_count=1,
            observation_executed=False,
        )


def test_mapping_rejects_usable_false_execution_flag():
    with pytest.raises(
        ValueError,
        match="usable source observation requires observation_executed to be True",
    ):
        SourceObservationResult.validate(
            _usable_mapping(observation_executed=False)
        )


def test_normalizer_rejects_usable_false_execution_flag():
    with pytest.raises(
        ValueError,
        match="usable source observation requires observation_executed to be True",
    ):
        SourceObservationResultNormalizer.normalize(
            _usable_mapping(observation_executed=False)
        )


def test_usable_true_execution_flag_remains_valid():
    result = SourceObservationResult.validate(
        _usable_mapping(observation_executed=True)
    )

    assert result.status == "usable"
    assert result.observation_executed is True
    assert result.source_count == 1


def test_non_boolean_execution_flag_remains_rejected():
    with pytest.raises(
        ValueError,
        match="observation_executed must be a boolean",
    ):
        SourceObservationResult.validate(
            _usable_mapping(observation_executed=1)
        )


def test_empty_result_may_explicitly_record_not_executed():
    result = SourceObservationResult(
        status="empty",
        observation_executed=False,
    )

    assert result.status == "empty"
    assert result.observation_executed is False
    assert result.source_count == 0


def test_unavailable_result_may_explicitly_record_not_executed():
    result = SourceObservationResult(
        status="unavailable",
        observation_executed=False,
        reason="observation_not_executed",
    )

    assert result.status == "unavailable"
    assert result.observation_executed is False
    assert result.reason == "observation_not_executed"


def test_existing_empty_helper_remains_executed_true():
    result = SourceObservationResult.empty_result()

    assert result.status == "empty"
    assert result.observation_executed is True


def test_existing_unavailable_helper_remains_executed_true():
    result = SourceObservationResult.unavailable_result(
        "source_provenance_unavailable"
    )

    assert result.status == "unavailable"
    assert result.observation_executed is True


def test_freshness_evaluator_rejects_mapping_that_denies_observation_execution():
    with pytest.raises(
        ValueError,
        match="usable source observation requires observation_executed to be True",
    ):
        SourceFreshnessEvaluator(clock=lambda: NOW).evaluate_result(
            _usable_mapping(observation_executed=False),
            max_age_seconds=3600,
        )


def test_freshness_evaluator_accepts_executed_observation_mapping():
    result = SourceFreshnessEvaluator(clock=lambda: NOW).evaluate_result(
        _usable_mapping(observation_executed=True),
        max_age_seconds=3600,
    )

    assert result.status == "usable"
    assert result.fresh_count == 1
    assert result.freshness_executed is True


def test_source_observation_builder_usable_result_records_execution_true():
    provenance = SourceProvenanceResult.usable_result(
        (
            SourceProvenance(
                source_id="source-1",
                source_ref="https://example.com",
                uri="https://example.com",
            ),
        )
    )
    result = SourceObservationBuilder(clock=lambda: NOW).build_result(
        provenance
    )

    assert result.status == "usable"
    assert result.observation_executed is True
    assert result.source_count == 1


def test_retrieval_observation_builder_usable_result_records_execution_true():
    provenance = SourceProvenanceResult.usable_result(
        (
            SourceProvenance(
                source_id="source-1",
                source_ref="https://example.com",
                uri="https://example.com",
            ),
        )
    )
    result = SourceObservationBuilder(clock=lambda: NOW).build_retrieval_result(
        provenance,
        [
            {
                "uri": "https://example.com",
                "observed_at": OBSERVED,
            }
        ],
        require_provider_observations=True,
    )

    assert result.status == "usable"
    assert result.observation_executed is True
    assert result.observations[0].observation_method == (
        "retrieval_provider_observation"
    )


def test_step189_timestamp_canonicalization_remains_intact():
    observation = SourceObservation(
        source_id="source-1",
        observed_at="2026-01-01T17:30:00+05:30",
        observation_method="retrieval_provider_observation",
    )

    assert observation.observed_at == OBSERVED


def test_step193_freshness_execution_integrity_remains_downstream():
    freshness = SourceFreshnessEvaluator(clock=lambda: NOW).evaluate_result(
        SourceObservationResult.usable_result((_observation(),)),
        max_age_seconds=3600,
    )

    assert freshness.status == "usable"
    assert freshness.freshness_executed is True
    assert freshness.fresh_count == 1
