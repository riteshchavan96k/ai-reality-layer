import pytest

from backend.app.reality.evidence_normalization_consumption_result import (
    EvidenceNormalizationConsumptionResult,
)
from backend.app.reality.evidence_normalization_consumer import EvidenceNormalizationConsumer


def test_completed_evidence_returns_explicit_result() -> None:
    result = EvidenceNormalizationConsumer().consume(
        {"status": "completed", "sources": [{"title": "Example"}], "content": "evidence"}
    )
    assert isinstance(result, EvidenceNormalizationConsumptionResult)
    assert result.status == "usable"
    assert result.usable is True
    assert result.evidence_status == "completed"
    assert result.consumption_evaluated is True


def test_not_required_returns_explicit_result() -> None:
    result = EvidenceNormalizationConsumer().consume(
        {"status": "not_required", "sources": [], "content": None}
    )
    assert result.to_dict() == {
        "status": "usable",
        "evidence_status": "not_required",
        "usable": True,
        "reason": None,
        "consumption_evaluated": True,
    }


def test_rejected_evidence_preserves_reason() -> None:
    result = EvidenceNormalizationConsumer().consume(
        {"status": "invalid_evidence", "sources": [], "content": None}
    )
    assert result.status == "rejected"
    assert result.usable is False
    assert result.reason == "invalid_evidence"


def test_empty_completed_evidence_is_explicitly_rejected() -> None:
    result = EvidenceNormalizationConsumer().consume(
        {"status": "completed", "sources": [], "content": None}
    )
    assert result.status == "rejected"
    assert result.reason == "empty_normalized_evidence"


def test_invalid_input_still_fails_closed() -> None:
    with pytest.raises(ValueError, match="normalized evidence must be a dictionary"):
        EvidenceNormalizationConsumer().consume(None)


def test_result_is_immutable() -> None:
    result = EvidenceNormalizationConsumptionResult.usable_result("completed")
    with pytest.raises((AttributeError, TypeError)):
        result.usable = False  # type: ignore[misc]


def test_result_rejects_inconsistent_state() -> None:
    with pytest.raises(ValueError, match="rejected status requires"):
        EvidenceNormalizationConsumptionResult(
            status="rejected", evidence_status="completed", usable=True
        )


def test_result_rejects_unknown_status() -> None:
    with pytest.raises(ValueError, match="status must be usable or rejected"):
        EvidenceNormalizationConsumptionResult(
            status="unknown", evidence_status="completed", usable=False
        )


def test_result_rejects_unknown_evidence_status() -> None:
    with pytest.raises(ValueError, match="supported evidence status"):
        EvidenceNormalizationConsumptionResult(
            status="rejected", evidence_status="future_state", usable=False
        )
