import pytest

from backend.app.reality.evidence_quality_validation import EvidenceQualityValidationResult
from backend.app.reality.evidence_quality_validation_normalizer import EvidenceQualityValidationResultNormalizer


def test_typed_result_is_preserved() -> None:
    result = EvidenceQualityValidationResult.usable_result(1, True, True)
    assert EvidenceQualityValidationResultNormalizer.normalize(result) is result


def test_usable_mapping_is_normalized() -> None:
    result = EvidenceQualityValidationResultNormalizer.normalize(
        {
            "status": "usable",
            "usable": True,
            "source_count": 2,
            "has_content": True,
            "provenance_complete": True,
            "issues": [],
        }
    )
    assert isinstance(result, EvidenceQualityValidationResult)
    assert result.status == "usable"
    assert result.source_count == 2


def test_insufficient_mapping_preserves_issues() -> None:
    result = EvidenceQualityValidationResultNormalizer.normalize(
        {
            "status": "insufficient",
            "usable": False,
            "source_count": 0,
            "has_content": False,
            "provenance_complete": True,
            "issues": ["no_sources", "no_content"],
        }
    )
    assert result.issues == ["no_sources", "no_content"]


def test_not_required_mapping_uses_default_execution_state() -> None:
    result = EvidenceQualityValidationResultNormalizer.normalize(
        {
            "status": "not_required",
            "usable": False,
            "source_count": 0,
            "has_content": False,
            "provenance_complete": True,
            "issues": [],
        }
    )
    assert result.status == "not_required"
    assert result.validation_executed is True


def test_unsupported_shape_is_rejected() -> None:
    with pytest.raises(ValueError, match="result must be a result contract or mapping"):
        EvidenceQualityValidationResultNormalizer.normalize(None)


def test_invalid_mapping_is_rejected_by_canonical_contract() -> None:
    with pytest.raises(ValueError):
        EvidenceQualityValidationResultNormalizer.normalize(
            {
                "status": "usable",
                "usable": False,
                "source_count": 1,
                "has_content": True,
                "provenance_complete": True,
                "issues": [],
            }
        )


def test_non_list_issues_are_rejected() -> None:
    with pytest.raises(ValueError, match="issues must be a list"):
        EvidenceQualityValidationResultNormalizer.normalize(
            {
                "status": "insufficient",
                "usable": False,
                "source_count": 1,
                "has_content": True,
                "provenance_complete": True,
                "issues": "no_sources",
            }
        )


def test_serialization_is_deterministic() -> None:
    result = EvidenceQualityValidationResultNormalizer.normalize(
        {
            "status": "insufficient",
            "usable": False,
            "source_count": 0,
            "has_content": False,
            "provenance_complete": False,
            "issues": ["no_sources"],
            "validation_executed": False,
        }
    )
    assert result.to_dict() == {
        "status": "insufficient",
        "usable": False,
        "source_count": 0,
        "has_content": False,
        "provenance_complete": False,
        "issues": ["no_sources"],
        "validation_executed": False,
    }
