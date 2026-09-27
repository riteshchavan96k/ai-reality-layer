from datetime import datetime, timezone

import pytest

from backend.app.reality.source_observation import SourceObservation, SourceObservationResult
from backend.app.reality.source_observation_builder import SourceObservationBuilder
from backend.app.reality.source_observation_normalizer import SourceObservationResultNormalizer
from backend.app.reality.source_provenance import SourceProvenance, SourceProvenanceResult


OBSERVED_AT = "2026-01-01T00:00:00Z"


def test_step158_accepts_canonical_source_observation_result():
    observation = SourceObservation("source-1", OBSERVED_AT)
    result = SourceObservationResult.usable_result((observation,))

    assert SourceObservationResult.validate(result) is result


def test_step158_normalizes_mapping():
    result = SourceObservationResultNormalizer.normalize(
        {
            "status": "usable",
            "observations": [
                {
                    "source_id": "source-1",
                    "observed_at": OBSERVED_AT,
                    "observation_method": "retrieval_observation",
                }
            ],
            "source_count": 1,
            "observation_executed": True,
            "reason": None,
        }
    )

    assert result.status == "usable"
    assert result.source_count == 1
    assert result.observations[0].source_id == "source-1"


def test_step158_rejects_missing_required_result_field():
    with pytest.raises(ValueError, match="missing required fields"):
        SourceObservationResult.validate(
            {
                "status": "usable",
                "observations": [],
                "source_count": 0,
            }
        )


def test_step158_rejects_malformed_nested_observation():
    with pytest.raises(ValueError, match="source observation is missing required fields"):
        SourceObservationResultNormalizer.normalize(
            {
                "status": "usable",
                "observations": [{"source_id": "source-1"}],
                "source_count": 1,
                "observation_executed": True,
                "reason": None,
            }
        )


def test_step158_rejects_future_observation():
    future = (datetime.now(timezone.utc).replace(year=datetime.now(timezone.utc).year + 1)).isoformat()
    with pytest.raises(ValueError, match="cannot be in the future"):
        SourceObservation("source-1", future)


def test_step158_builder_returns_canonical_validated_result():
    provenance = SourceProvenanceResult.usable_result(
        (
            SourceProvenance(
                source_id="source-1",
                source_ref="https://example.com",
                uri="https://example.com",
            ),
        )
    )
    fixed_clock = lambda: datetime(2026, 1, 1, tzinfo=timezone.utc)

    result = SourceObservationBuilder(clock=fixed_clock).build_result(provenance)

    assert isinstance(result, SourceObservationResult)
    assert result.status == "usable"
    assert result.source_count == 1
    assert result.observations[0].observed_at == OBSERVED_AT
