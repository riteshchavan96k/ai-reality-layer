import pytest

from backend.app.reality.evidence_normalization_consumption import EvidenceNormalizationConsumption
from backend.app.reality.evidence_normalization_consumer import EvidenceNormalizationConsumer


def test_completed_normalized_evidence_is_usable() -> None:
    result = EvidenceNormalizationConsumer().consume(
        {"status": "completed", "sources": [{"title": "Example"}], "content": "evidence"}
    )
    assert result.status == "usable"
    assert result.usable is True
    assert result.evidence_status == "completed"


def test_not_required_normalized_evidence_is_usable() -> None:
    result = EvidenceNormalizationConsumer().consume(
        {"status": "not_required", "sources": [], "content": None}
    )
    assert result.status == "usable"
    assert result.evidence_status == "not_required"


def test_empty_completed_evidence_is_rejected() -> None:
    result = EvidenceNormalizationConsumer().consume(
        {"status": "completed", "sources": [], "content": None}
    )
    assert result.status == "rejected"
    assert result.reason == "empty_normalized_evidence"


def test_invalid_evidence_is_rejected() -> None:
    result = EvidenceNormalizationConsumer().consume(
        {"status": "invalid_evidence", "sources": [], "content": None}
    )
    assert result.usable is False
    assert result.reason == "invalid_evidence"


def test_unknown_evidence_is_rejected() -> None:
    result = EvidenceNormalizationConsumer().consume(
        {"status": "unknown", "sources": [], "content": None}
    )
    assert result.status == "rejected"
    assert result.reason == "unknown_evidence_status"


def test_invalid_sources_are_rejected() -> None:
    result = EvidenceNormalizationConsumer().consume(
        {"status": "completed", "sources": {}, "content": "evidence"}
    )
    assert result.reason == "invalid_normalized_evidence_sources"


def test_invalid_content_is_rejected() -> None:
    result = EvidenceNormalizationConsumer().consume(
        {"status": "completed", "sources": [{"title": "Example"}], "content": 123}
    )
    assert result.reason == "invalid_normalized_evidence_content"


def test_unsupported_status_is_rejected() -> None:
    result = EvidenceNormalizationConsumer().consume(
        {"status": "future_state", "sources": [], "content": None}
    )
    assert result.reason == "unsupported_evidence_status"


def test_invalid_input_is_rejected() -> None:
    with pytest.raises(ValueError, match="normalized evidence must be a dictionary"):
        EvidenceNormalizationConsumer().consume([])


def test_consumption_contract_is_immutable_and_serializable() -> None:
    result = EvidenceNormalizationConsumption.usable_result("completed")
    assert result.to_dict() == {
        "status": "usable",
        "evidence_status": "completed",
        "usable": True,
        "reason": None,
        "consumption_executed": True,
    }
    with pytest.raises((AttributeError, TypeError)):
        result.usable = False  # type: ignore[misc]


def test_consumption_contract_rejects_inconsistent_state() -> None:
    with pytest.raises(ValueError, match="usable status requires"):
        EvidenceNormalizationConsumption(
            status="usable", evidence_status="completed", usable=False
        )
