"""Step 201 — canonical evidence-normalization consumption execution integrity."""

import pytest

from backend.app.reality.evidence_normalization import EvidenceNormalizationResult
from backend.app.reality.evidence_normalization_consumer import (
    EvidenceNormalizationConsumer,
)
from backend.app.reality.evidence_normalization_consumption import (
    EvidenceNormalizationConsumption,
)
from backend.app.reality.evidence_normalization_consumption_normalizer import (
    EvidenceNormalizationConsumptionNormalizer,
)
from backend.app.reality.evidence_normalization_consumption_result import (
    EvidenceNormalizationConsumptionResult,
)


SOURCE = "https://example.com"
CONTENT = "The service is operational."


def _usable_mapping(*, consumption_executed: object) -> dict:
    return {
        "status": "usable",
        "evidence_status": "completed",
        "usable": True,
        "reason": None,
        "consumption_executed": consumption_executed,
    }


def _completed_evidence() -> EvidenceNormalizationResult:
    return EvidenceNormalizationResult(
        status="completed",
        sources=[{"uri": SOURCE}],
        content=CONTENT,
        source_count=1,
        has_content=True,
        normalization_executed=True,
    )


def test_usable_consumption_rejects_false_execution_flag():
    with pytest.raises(
        ValueError,
        match=(
            "usable evidence normalization consumption requires "
            "consumption_executed to be True"
        ),
    ):
        EvidenceNormalizationConsumption(
            status="usable",
            evidence_status="completed",
            usable=True,
            consumption_executed=False,
        )


def test_mapping_rejects_usable_false_execution_flag():
    with pytest.raises(
        ValueError,
        match=(
            "usable evidence normalization consumption requires "
            "consumption_executed to be True"
        ),
    ):
        EvidenceNormalizationConsumption.validate(
            _usable_mapping(consumption_executed=False)
        )


def test_normalizer_rejects_usable_false_execution_mapping():
    with pytest.raises(
        ValueError,
        match=(
            "usable evidence normalization consumption requires "
            "consumption_executed to be True"
        ),
    ):
        EvidenceNormalizationConsumptionNormalizer.normalize(
            _usable_mapping(consumption_executed=False)
        )


def test_legacy_result_adapter_rejects_usable_not_evaluated_result():
    legacy = EvidenceNormalizationConsumptionResult(
        status="usable",
        evidence_status="completed",
        usable=True,
        consumption_evaluated=False,
    )

    with pytest.raises(
        ValueError,
        match=(
            "usable evidence normalization consumption requires "
            "consumption_executed to be True"
        ),
    ):
        EvidenceNormalizationConsumptionNormalizer.normalize(legacy)


def test_usable_true_execution_flag_remains_valid():
    result = EvidenceNormalizationConsumption.validate(
        _usable_mapping(consumption_executed=True)
    )

    assert result.status == "usable"
    assert result.usable is True
    assert result.consumption_executed is True


def test_non_boolean_execution_flag_remains_rejected():
    with pytest.raises(
        ValueError,
        match="consumption_executed must be a boolean",
    ):
        EvidenceNormalizationConsumption.validate(
            _usable_mapping(consumption_executed=1)
        )


def test_rejected_consumption_may_explicitly_record_not_executed():
    result = EvidenceNormalizationConsumption(
        status="rejected",
        evidence_status="unknown",
        usable=False,
        reason="consumption_not_executed",
        consumption_executed=False,
    )

    assert result.status == "rejected"
    assert result.usable is False
    assert result.consumption_executed is False


def test_existing_usable_helper_remains_executed_true():
    result = EvidenceNormalizationConsumption.usable_result("completed")

    assert result.status == "usable"
    assert result.usable is True
    assert result.consumption_executed is True


def test_existing_rejected_helper_remains_executed_true():
    result = EvidenceNormalizationConsumption.rejected_result(
        "invalid_evidence",
        "invalid_evidence",
    )

    assert result.status == "rejected"
    assert result.usable is False
    assert result.consumption_executed is True


def test_production_consumer_completed_path_normalizes_to_executed_usable():
    raw = EvidenceNormalizationConsumer().consume(_completed_evidence().to_dict())
    result = EvidenceNormalizationConsumptionNormalizer.normalize(raw)

    assert raw.status == "usable"
    assert raw.consumption_evaluated is True
    assert result.status == "usable"
    assert result.usable is True
    assert result.consumption_executed is True


def test_production_consumer_not_required_path_normalizes_to_executed_usable():
    evidence = EvidenceNormalizationResult(
        status="not_required",
        sources=[],
        content=None,
        source_count=0,
        has_content=False,
        normalization_executed=True,
    )
    raw = EvidenceNormalizationConsumer().consume(evidence.to_dict())
    result = EvidenceNormalizationConsumptionNormalizer.normalize(raw)

    assert raw.status == "usable"
    assert raw.consumption_evaluated is True
    assert result.status == "usable"
    assert result.evidence_status == "not_required"
    assert result.consumption_executed is True


def test_production_consumer_invalid_evidence_path_remains_rejected():
    evidence = EvidenceNormalizationResult(
        status="invalid_evidence",
        sources=[],
        content=None,
        source_count=0,
        has_content=False,
        normalization_executed=True,
    )
    raw = EvidenceNormalizationConsumer().consume(evidence.to_dict())
    result = EvidenceNormalizationConsumptionNormalizer.normalize(raw)

    assert raw.status == "rejected"
    assert raw.consumption_evaluated is True
    assert result.status == "rejected"
    assert result.usable is False
    assert result.consumption_executed is True


def test_production_consumer_empty_completed_evidence_remains_rejected():
    evidence = EvidenceNormalizationResult(
        status="completed",
        sources=[],
        content=None,
        source_count=0,
        has_content=False,
        normalization_executed=True,
    )
    raw = EvidenceNormalizationConsumer().consume(evidence.to_dict())
    result = EvidenceNormalizationConsumptionNormalizer.normalize(raw)

    assert result.status == "rejected"
    assert result.usable is False
    assert result.reason == "empty_normalized_evidence"


def test_existing_status_usability_integrity_remains_intact():
    with pytest.raises(
        ValueError,
        match="usable status requires usable=True",
    ):
        EvidenceNormalizationConsumption(
            status="usable",
            evidence_status="completed",
            usable=False,
            consumption_executed=True,
        )


def test_upstream_noncompleted_execution_flexibility_remains_unchanged():
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
