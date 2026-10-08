"""Step 202 — canonical evidence-normalization execution-state integrity."""

import pytest

from backend.app.reality.evidence_normalization import EvidenceNormalizationResult
from backend.app.reality.evidence_normalization_consumer import (
    EvidenceNormalizationConsumer,
)
from backend.app.reality.evidence_normalization_consumption_normalizer import (
    EvidenceNormalizationConsumptionNormalizer,
)
from backend.app.reality.evidence_normalizer import RetrievalEvidenceNormalizer


SOURCE = "https://example.com"
CONTENT = "The service is operational."


def _completed_mapping(*, normalization_executed: object) -> dict:
    return {
        "status": "completed",
        "sources": [{"uri": SOURCE}],
        "content": CONTENT,
        "source_count": 1,
        "has_content": True,
        "normalization_executed": normalization_executed,
    }


def test_completed_result_rejects_false_execution_flag():
    with pytest.raises(
        ValueError,
        match=(
            "completed evidence normalization requires "
            "normalization_executed to be True"
        ),
    ):
        EvidenceNormalizationResult(
            status="completed",
            sources=[{"uri": SOURCE}],
            content=CONTENT,
            source_count=1,
            has_content=True,
            normalization_executed=False,
        )


def test_mapping_validation_rejects_completed_false_execution_flag():
    with pytest.raises(
        ValueError,
        match=(
            "completed evidence normalization requires "
            "normalization_executed to be True"
        ),
    ):
        EvidenceNormalizationResult.validate(
            _completed_mapping(normalization_executed=False)
        )


def test_from_mapping_rejects_completed_false_execution_flag():
    with pytest.raises(
        ValueError,
        match=(
            "completed evidence normalization requires "
            "normalization_executed to be True"
        ),
    ):
        EvidenceNormalizationResult.from_mapping(
            _completed_mapping(normalization_executed=False)
        )


def test_completed_true_execution_flag_remains_valid():
    result = EvidenceNormalizationResult.validate(
        _completed_mapping(normalization_executed=True)
    )

    assert result.status == "completed"
    assert result.normalization_executed is True
    assert result.source_count == 1
    assert result.has_content is True


def test_non_boolean_execution_flag_remains_rejected():
    with pytest.raises(
        ValueError,
        match="normalization_executed must be a boolean",
    ):
        EvidenceNormalizationResult.validate(
            _completed_mapping(normalization_executed=1)
        )


def test_not_required_result_may_explicitly_record_not_executed():
    result = EvidenceNormalizationResult(
        status="not_required",
        sources=[],
        content=None,
        source_count=0,
        has_content=False,
        normalization_executed=False,
    )

    assert result.status == "not_required"
    assert result.normalization_executed is False


def test_invalid_evidence_result_may_explicitly_record_not_executed():
    result = EvidenceNormalizationResult(
        status="invalid_evidence",
        sources=[],
        content=None,
        source_count=0,
        has_content=False,
        normalization_executed=False,
    )

    assert result.status == "invalid_evidence"
    assert result.normalization_executed is False


def test_unknown_result_may_explicitly_record_not_executed():
    result = EvidenceNormalizationResult(
        status="unknown",
        sources=[],
        content=None,
        source_count=0,
        has_content=False,
        normalization_executed=False,
    )

    assert result.status == "unknown"
    assert result.normalization_executed is False


def test_consumer_rejects_completed_mapping_that_denies_normalization_execution():
    with pytest.raises(
        ValueError,
        match=(
            "completed evidence normalization requires "
            "normalization_executed to be True"
        ),
    ):
        EvidenceNormalizationConsumer().consume(
            _completed_mapping(normalization_executed=False)
        )


def test_consumer_preserves_legacy_completed_mapping_compatibility():
    raw_consumption = EvidenceNormalizationConsumer().consume(
        {
            "status": "completed",
            "sources": [{"uri": SOURCE}],
            "content": CONTENT,
        }
    )
    consumption = EvidenceNormalizationConsumptionNormalizer.normalize(
        raw_consumption
    )

    assert consumption.status == "usable"
    assert consumption.evidence_status == "completed"
    assert consumption.consumption_executed is True


def test_consumer_preserves_legacy_invalid_source_rejection():
    raw_consumption = EvidenceNormalizationConsumer().consume(
        {
            "status": "completed",
            "sources": {},
            "content": CONTENT,
        }
    )

    assert raw_consumption.status == "rejected"
    assert raw_consumption.reason == "invalid_normalized_evidence_sources"


def test_consumer_preserves_legacy_invalid_input_error():
    with pytest.raises(
        ValueError,
        match="normalized evidence must be a dictionary",
    ):
        EvidenceNormalizationConsumer().consume(None)


def test_consumer_accepts_canonical_typed_completed_result():
    evidence = EvidenceNormalizationResult.validate(
        _completed_mapping(normalization_executed=True)
    )

    raw_consumption = EvidenceNormalizationConsumer().consume(evidence)
    consumption = EvidenceNormalizationConsumptionNormalizer.normalize(
        raw_consumption
    )

    assert raw_consumption.status == "usable"
    assert consumption.status == "usable"
    assert consumption.usable is True
    assert consumption.consumption_executed is True


def test_consumer_accepts_canonical_completed_mapping():
    raw_consumption = EvidenceNormalizationConsumer().consume(
        _completed_mapping(normalization_executed=True)
    )
    consumption = EvidenceNormalizationConsumptionNormalizer.normalize(
        raw_consumption
    )

    assert consumption.status == "usable"
    assert consumption.evidence_status == "completed"
    assert consumption.consumption_executed is True


def test_not_required_nonexecuted_normalization_remains_nonpositive_downstream():
    evidence = EvidenceNormalizationResult(
        status="not_required",
        sources=[],
        content=None,
        source_count=0,
        has_content=False,
        normalization_executed=False,
    )

    raw_consumption = EvidenceNormalizationConsumer().consume(evidence)
    consumption = EvidenceNormalizationConsumptionNormalizer.normalize(
        raw_consumption
    )

    assert consumption.status == "usable"
    assert consumption.evidence_status == "not_required"
    assert consumption.consumption_executed is True


def test_invalid_evidence_nonexecuted_normalization_remains_rejected():
    evidence = EvidenceNormalizationResult(
        status="invalid_evidence",
        sources=[],
        content=None,
        source_count=0,
        has_content=False,
        normalization_executed=False,
    )

    raw_consumption = EvidenceNormalizationConsumer().consume(evidence)
    consumption = EvidenceNormalizationConsumptionNormalizer.normalize(
        raw_consumption
    )

    assert consumption.status == "rejected"
    assert consumption.usable is False
    assert consumption.reason == "invalid_evidence"


def test_unknown_nonexecuted_normalization_remains_rejected():
    evidence = EvidenceNormalizationResult(
        status="unknown",
        sources=[],
        content=None,
        source_count=0,
        has_content=False,
        normalization_executed=False,
    )

    raw_consumption = EvidenceNormalizationConsumer().consume(evidence)
    consumption = EvidenceNormalizationConsumptionNormalizer.normalize(
        raw_consumption
    )

    assert consumption.status == "rejected"
    assert consumption.usable is False
    assert consumption.reason == "unknown_evidence_status"


def test_production_normalizer_completed_result_records_execution_true():
    result = RetrievalEvidenceNormalizer().normalize_result(
        {
            "status": "completed",
            "sources": [{"uri": SOURCE}],
            "content": CONTENT,
        }
    )

    assert result.status == "completed"
    assert result.normalization_executed is True
    assert result.source_count == 1
    assert result.has_content is True


def test_production_normalizer_invalid_evidence_result_records_execution_true():
    result = RetrievalEvidenceNormalizer().normalize_result(
        {
            "status": "completed",
            "sources": [],
            "content": None,
        }
    )

    assert result.status == "invalid_evidence"
    assert result.normalization_executed is True


def test_production_normalizer_not_required_result_records_execution_true():
    result = RetrievalEvidenceNormalizer().normalize_result(
        {
            "status": "not_required",
            "sources": [],
            "content": None,
        }
    )

    assert result.status == "not_required"
    assert result.normalization_executed is True


def test_existing_source_count_integrity_remains_intact():
    with pytest.raises(
        ValueError,
        match="source_count must match the number of sources",
    ):
        EvidenceNormalizationResult(
            status="completed",
            sources=[{"uri": SOURCE}],
            content=CONTENT,
            source_count=0,
            has_content=True,
            normalization_executed=True,
        )


def test_existing_content_presence_integrity_remains_intact():
    with pytest.raises(
        ValueError,
        match="has_content must match content presence",
    ):
        EvidenceNormalizationResult(
            status="completed",
            sources=[{"uri": SOURCE}],
            content=CONTENT,
            source_count=1,
            has_content=False,
            normalization_executed=True,
        )


def test_step201_consumption_execution_integrity_remains_downstream():
    evidence = EvidenceNormalizationResult.validate(
        _completed_mapping(normalization_executed=True)
    )
    raw_consumption = EvidenceNormalizationConsumer().consume(evidence)
    consumption = EvidenceNormalizationConsumptionNormalizer.normalize(
        raw_consumption
    )

    assert consumption.status == "usable"
    assert consumption.consumption_executed is True
