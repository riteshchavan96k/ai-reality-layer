import pytest

from backend.app.reality.evidence_normalization import EvidenceNormalizationResult
from backend.app.reality.evidence_normalizer import RetrievalEvidenceNormalizer


def test_normalize_result_returns_canonical_contract() -> None:
    result = RetrievalEvidenceNormalizer().normalize_result(
        {
            "status": "completed",
            "sources": [{"title": "Example", "uri": "https://example.com"}],
            "content": "evidence",
        }
    )
    assert isinstance(result, EvidenceNormalizationResult)
    assert result.status == "completed"
    assert result.source_count == 1
    assert result.has_content is True


def test_normalize_preserves_legacy_dictionary_api() -> None:
    result = RetrievalEvidenceNormalizer().normalize(
        {"status": "completed", "sources": [], "content": "evidence"}
    )
    assert isinstance(result, dict)
    assert result["status"] == "completed"
    assert result["has_content"] is True


def test_empty_completed_retrieval_becomes_invalid_evidence() -> None:
    result = RetrievalEvidenceNormalizer().normalize_result(
        {"status": "completed", "sources": [], "content": None}
    )
    assert result.status == "invalid_evidence"
    assert result.source_count == 0
    assert result.has_content is False


def test_not_required_is_represented_explicitly() -> None:
    result = RetrievalEvidenceNormalizer().normalize_result(
        {"status": "not_required", "sources": [], "content": None}
    )
    assert result.status == "not_required"


def test_unknown_status_is_normalized_to_unknown() -> None:
    result = RetrievalEvidenceNormalizer().normalize_result(
        {"status": None, "sources": [], "content": None}
    )
    assert result.status == "unknown"


def test_invalid_sources_are_rejected() -> None:
    with pytest.raises(ValueError, match="retrieval sources must be a list"):
        RetrievalEvidenceNormalizer().normalize_result(
            {"status": "completed", "sources": {}, "content": "evidence"}
        )


def test_invalid_source_shape_is_rejected() -> None:
    with pytest.raises(ValueError, match="each retrieval source must be a dictionary"):
        RetrievalEvidenceNormalizer().normalize_result(
            {"status": "completed", "sources": ["bad"], "content": "evidence"}
        )


def test_source_provenance_is_normalized_to_strings() -> None:
    result = RetrievalEvidenceNormalizer().normalize_result(
        {
            "status": "completed",
            "sources": [{"title": 123, "uri": 456}],
            "content": "evidence",
        }
    )
    assert result.sources == [{"title": "123", "uri": "456"}]


def test_contract_serialization_is_deterministic() -> None:
    result = EvidenceNormalizationResult(
        status="completed",
        sources=[{"title": "Example", "uri": "https://example.com"}],
        content="evidence",
        source_count=1,
        has_content=True,
    )
    assert result.to_dict() == {
        "status": "completed",
        "sources": [{"title": "Example", "uri": "https://example.com"}],
        "content": "evidence",
        "source_count": 1,
        "has_content": True,
        "normalization_executed": True,
    }


def test_contract_is_immutable() -> None:
    result = EvidenceNormalizationResult(
        status="completed", sources=[], content="evidence", source_count=0, has_content=True
    )
    with pytest.raises((AttributeError, TypeError)):
        result.status = "unknown"  # type: ignore[misc]


def test_contract_rejects_inconsistent_source_count() -> None:
    with pytest.raises(ValueError, match="source_count"):
        EvidenceNormalizationResult(
            status="completed", sources=[{"title": "x"}], content="evidence", source_count=0, has_content=True
        )


def test_contract_validate_accepts_canonical_result() -> None:
    result = EvidenceNormalizationResult(
        status="completed",
        sources=[{"title": "Example", "uri": "https://example.com"}],
        content="evidence",
        source_count=1,
        has_content=True,
    )
    assert EvidenceNormalizationResult.validate(result) is result


def test_contract_validate_accepts_mapping() -> None:
    result = EvidenceNormalizationResult.validate(
        {
            "status": "completed",
            "sources": [{"title": "Example"}],
            "content": "evidence",
            "source_count": 1,
            "has_content": True,
            "normalization_executed": True,
        }
    )
    assert result.status == "completed"
    assert result.source_count == 1


def test_contract_validate_rejects_missing_required_field() -> None:
    with pytest.raises(ValueError, match="missing required fields"):
        EvidenceNormalizationResult.validate(
            {
                "status": "completed",
                "sources": [],
                "content": None,
                "source_count": 0,
                "has_content": False,
            }
        )


def test_contract_validate_rejects_inconsistent_has_content() -> None:
    with pytest.raises(ValueError, match="has_content must match content presence"):
        EvidenceNormalizationResult.validate(
            {
                "status": "completed",
                "sources": [],
                "content": "evidence",
                "source_count": 0,
                "has_content": False,
                "normalization_executed": True,
            }
        )


def test_contract_validate_rejects_inconsistent_source_count() -> None:
    with pytest.raises(ValueError, match="source_count must match"):
        EvidenceNormalizationResult.validate(
            {
                "status": "completed",
                "sources": [{"title": "Example"}],
                "content": "evidence",
                "source_count": 0,
                "has_content": True,
                "normalization_executed": True,
            }
        )
