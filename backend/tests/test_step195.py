"""Step 195 — canonical source-provenance execution-state integrity."""

from datetime import datetime, timezone
import hashlib

import pytest

from backend.app.reality.source_observation_builder import SourceObservationBuilder
from backend.app.reality.source_freshness_evaluator import SourceFreshnessEvaluator
from backend.app.reality.source_provenance import (
    SourceProvenance,
    SourceProvenanceResult,
)
from backend.app.reality.source_provenance_builder import SourceProvenanceBuilder
from backend.app.reality.source_provenance_normalizer import (
    SourceProvenanceResultNormalizer,
)


URI = "https://example.com"
OBSERVED = "2026-01-01T12:00:00Z"
NOW = datetime(2026, 1, 1, 12, 30, tzinfo=timezone.utc)


def _source() -> SourceProvenance:
    return SourceProvenance(
        source_id=hashlib.sha256(URI.encode("utf-8")).hexdigest(),
        source_ref=URI,
        uri=URI,
        title="Example",
    )


def _usable_mapping(*, provenance_executed: object) -> dict:
    return {
        "status": "usable",
        "sources": [_source().to_dict()],
        "source_count": 1,
        "provenance_executed": provenance_executed,
        "reason": None,
    }


def test_usable_result_rejects_false_execution_flag():
    with pytest.raises(
        ValueError,
        match="usable source provenance requires provenance_executed to be True",
    ):
        SourceProvenanceResult(
            status="usable",
            sources=(_source(),),
            source_count=1,
            provenance_executed=False,
        )


def test_mapping_rejects_usable_false_execution_flag():
    with pytest.raises(
        ValueError,
        match="usable source provenance requires provenance_executed to be True",
    ):
        SourceProvenanceResult.validate(
            _usable_mapping(provenance_executed=False)
        )


def test_normalizer_rejects_usable_false_execution_flag():
    with pytest.raises(
        ValueError,
        match="usable source provenance requires provenance_executed to be True",
    ):
        SourceProvenanceResultNormalizer.normalize(
            _usable_mapping(provenance_executed=False)
        )


def test_usable_true_execution_flag_remains_valid():
    result = SourceProvenanceResult.validate(
        _usable_mapping(provenance_executed=True)
    )

    assert result.status == "usable"
    assert result.provenance_executed is True
    assert result.source_count == 1


def test_non_boolean_execution_flag_remains_rejected():
    with pytest.raises(
        ValueError,
        match="provenance_executed must be a boolean",
    ):
        SourceProvenanceResult.validate(
            _usable_mapping(provenance_executed=1)
        )


def test_empty_result_may_explicitly_record_not_executed():
    result = SourceProvenanceResult(
        status="empty",
        provenance_executed=False,
    )

    assert result.status == "empty"
    assert result.provenance_executed is False
    assert result.source_count == 0


def test_unavailable_result_may_explicitly_record_not_executed():
    result = SourceProvenanceResult(
        status="unavailable",
        provenance_executed=False,
        reason="provenance_not_executed",
    )

    assert result.status == "unavailable"
    assert result.provenance_executed is False
    assert result.reason == "provenance_not_executed"


def test_existing_empty_helper_remains_executed_true():
    result = SourceProvenanceResult.empty_result()

    assert result.status == "empty"
    assert result.provenance_executed is True


def test_existing_unavailable_helper_remains_executed_true():
    result = SourceProvenanceResult.unavailable_result(
        "evidence_not_usable"
    )

    assert result.status == "unavailable"
    assert result.provenance_executed is True


def test_observation_builder_rejects_mapping_that_denies_provenance_execution():
    with pytest.raises(
        ValueError,
        match="usable source provenance requires provenance_executed to be True",
    ):
        SourceObservationBuilder(clock=lambda: NOW).build_result(
            _usable_mapping(provenance_executed=False)
        )


def test_retrieval_observation_builder_rejects_mapping_that_denies_provenance_execution():
    with pytest.raises(
        ValueError,
        match="usable source provenance requires provenance_executed to be True",
    ):
        SourceObservationBuilder(clock=lambda: NOW).build_retrieval_result(
            _usable_mapping(provenance_executed=False),
            [{"uri": URI, "observed_at": OBSERVED}],
            require_provider_observations=True,
        )


def test_observation_and_freshness_accept_valid_executed_provenance():
    observations = SourceObservationBuilder(clock=lambda: NOW).build_retrieval_result(
        _usable_mapping(provenance_executed=True),
        [{"uri": URI, "observed_at": OBSERVED}],
        require_provider_observations=True,
    )
    freshness = SourceFreshnessEvaluator(clock=lambda: NOW).evaluate_result(
        observations,
        max_age_seconds=3600,
    )

    assert observations.status == "usable"
    assert observations.observation_executed is True
    assert freshness.status == "usable"
    assert freshness.freshness_executed is True
    assert freshness.fresh_count == 1


def test_source_provenance_builder_usable_result_records_execution_true():
    result = SourceProvenanceBuilder().build_result(
        {
            "status": "usable",
            "sources": [
                {
                    "uri": URI,
                    "title": "Example",
                }
            ],
        }
    )

    assert result.status == "usable"
    assert result.provenance_executed is True
    assert result.source_count == 1


def test_step194_observation_execution_integrity_remains_downstream():
    provenance = SourceProvenanceResult.usable_result((_source(),))
    observations = SourceObservationBuilder(clock=lambda: NOW).build_result(
        provenance
    )

    assert observations.status == "usable"
    assert observations.observation_executed is True


def test_step193_freshness_execution_integrity_remains_downstream():
    provenance = SourceProvenanceResult.usable_result((_source(),))
    observations = SourceObservationBuilder(clock=lambda: NOW).build_retrieval_result(
        provenance,
        [{"uri": URI, "observed_at": OBSERVED}],
        require_provider_observations=True,
    )
    freshness = SourceFreshnessEvaluator(clock=lambda: NOW).evaluate_result(
        observations,
        max_age_seconds=3600,
    )

    assert freshness.status == "usable"
    assert freshness.freshness_executed is True
