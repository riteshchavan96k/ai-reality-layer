import pytest

from backend.app.reality.evidence_quality import EvidenceQualityValidator
from backend.app.reality.evidence_quality_validation import EvidenceQualityValidationResult


def test_usable_evidence_returns_typed_result() -> None:
    result = EvidenceQualityValidator().validate_result(
        {
            "status": "completed",
            "sources": [{"title": "Example", "uri": "https://example.com/source"}],
            "content": "verified evidence",
        }
    )
    assert isinstance(result, EvidenceQualityValidationResult)
    assert result.status == "usable"
    assert result.usable is True
    assert result.source_count == 1
    assert result.has_content is True
    assert result.provenance_complete is True
    assert result.issues == []


def test_insufficient_evidence_returns_typed_result() -> None:
    result = EvidenceQualityValidator().validate_result(
        {"status": "completed", "sources": [], "content": "evidence"}
    )
    assert result.status == "insufficient"
    assert result.usable is False
    assert "no_sources" in result.issues


def test_invalid_uri_is_reported() -> None:
    result = EvidenceQualityValidator().validate_result(
        {
            "status": "completed",
            "sources": [{"title": "Example", "uri": "not-a-uri"}],
            "content": "evidence",
        }
    )
    assert result.status == "insufficient"
    assert result.provenance_complete is False
    assert "source_invalid_uri" in result.issues


def test_missing_provenance_is_reported() -> None:
    result = EvidenceQualityValidator().validate_result(
        {"status": "completed", "sources": [{}], "content": "evidence"}
    )
    assert result.status == "insufficient"
    assert "source_missing_provenance" in result.issues
    assert "incomplete_provenance" in result.issues


def test_not_required_returns_explicit_non_usable_result() -> None:
    result = EvidenceQualityValidator().validate_result(
        {"status": "not_required", "sources": [], "content": None}
    )
    assert result.status == "not_required"
    assert result.usable is False
    assert result.issues == []


def test_non_completed_evidence_is_insufficient() -> None:
    result = EvidenceQualityValidator().validate_result(
        {"status": "invalid_evidence", "sources": [], "content": None}
    )
    assert result.status == "insufficient"
    assert "retrieval_not_completed" in result.issues


def test_legacy_validate_api_uses_typed_contract() -> None:
    evidence = {
        "status": "completed",
        "sources": [{"title": "Example", "uri": "https://example.com/source"}],
        "content": "evidence",
    }
    assert EvidenceQualityValidator().validate(evidence) == EvidenceQualityValidator().validate_result(evidence).to_dict()


def test_invalid_input_is_rejected() -> None:
    with pytest.raises(ValueError, match="evidence must be a dictionary"):
        EvidenceQualityValidator().validate_result(None)  # type: ignore[arg-type]


def test_invalid_source_shape_is_rejected() -> None:
    with pytest.raises(ValueError, match="each evidence source must be a dictionary"):
        EvidenceQualityValidator().validate_result(
            {"status": "completed", "sources": ["invalid"], "content": "evidence"}
        )


def test_result_is_immutable_and_serializable() -> None:
    result = EvidenceQualityValidationResult.usable_result(1, True, True)
    assert result.to_dict() == {
        "status": "usable",
        "usable": True,
        "source_count": 1,
        "has_content": True,
        "provenance_complete": True,
        "issues": [],
        "validation_executed": True,
    }
    with pytest.raises((AttributeError, TypeError)):
        result.usable = False  # type: ignore[misc]


def test_result_rejects_inconsistent_state() -> None:
    with pytest.raises(ValueError, match="non-usable status requires"):
        EvidenceQualityValidationResult(
            status="insufficient",
            usable=True,
            source_count=1,
            has_content=True,
            provenance_complete=True,
            issues=[],
        )
