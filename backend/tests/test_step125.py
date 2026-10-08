import pytest

from backend.app.reality.claim_extraction import ClaimExtractionResult, EvidenceClaim
from backend.app.reality.claim_extractor import EvidenceClaimExtractor


def test_claim_contract_is_immutable_and_serializable():
    claim = EvidenceClaim("The system is available.", ("https://example.com",))
    assert claim.to_dict() == {
        "text": "The system is available.",
        "source_refs": ["https://example.com"],
        "extraction_method": "deterministic_sentence_split",
        "semantic_structure": {
            "status": "unstructured",
            "subject": None,
            "predicate": None,
            "object": None,
            "structuring_method": "not_attempted",
            "reason": "semantic_structuring_not_attempted",
        },
    }
    with pytest.raises(Exception):
        claim.text = "changed"


def test_extractor_splits_sentences_and_preserves_source_refs():
    result = EvidenceClaimExtractor().extract_result(
        {
            "status": "usable",
            "content": "Alpha is true. Beta is current! Alpha is true.",
            "sources": [{"title": "Source", "uri": "https://example.com/source"}],
        }
    )
    assert isinstance(result, ClaimExtractionResult)
    assert result.status == "usable"
    assert [claim.text for claim in result.claims] == ["Alpha is true.", "Beta is current!"]
    assert result.claims[0].source_refs == ("https://example.com/source",)
    assert result.to_dict()["claim_count"] == 2


def test_extractor_rejects_ambiguous_multi_source_attribution():
    # Historical behavior assigned both URIs to every claim even though the
    # combined text did not say which source supplied each statement. Step 182
    # intentionally closes that provenance-integrity hole.
    result = EvidenceClaimExtractor().extract_result(
        {
            "status": "usable",
            "content": "A documented statement.",
            "sources": [
                {"title": "A", "uri": "https://a.example"},
                {"title": "B", "uri": "https://b.example"},
            ],
        }
    )
    assert result.status == "unavailable"
    assert result.reason == "ambiguous_source_attribution"
    assert result.claims == ()
    assert result.source_count == 2


def test_non_usable_evidence_is_not_presented_as_claims():
    result = EvidenceClaimExtractor().extract_result(
        {"status": "invalid_evidence", "sources": [], "content": None, "reason": "no_evidence"}
    )
    assert result.status == "unavailable"
    assert result.claims == ()
    assert result.reason == "no_evidence"


def test_empty_content_returns_empty_result():
    result = EvidenceClaimExtractor().extract_result(
        {"status": "usable", "sources": [], "content": "   "}
    )
    assert result.status == "empty"
    assert result.claims == ()


def test_invalid_evidence_shape_is_rejected():
    with pytest.raises(ValueError, match="evidence must be a dictionary"):
        EvidenceClaimExtractor().extract_result("invalid")


def test_invalid_source_shape_is_rejected():
    with pytest.raises(ValueError, match="each evidence source must be a dictionary"):
        EvidenceClaimExtractor().extract_result(
            {"status": "usable", "content": "A statement.", "sources": ["invalid"]}
        )


def test_claim_result_rejects_inconsistent_states():
    claim = EvidenceClaim("A statement.")
    with pytest.raises(ValueError, match="usable claim extraction requires"):
        ClaimExtractionResult("usable", claims=())
    with pytest.raises(ValueError, match="empty claim extraction cannot"):
        ClaimExtractionResult("empty", claims=(claim,))
    with pytest.raises(ValueError, match="requires a reason"):
        ClaimExtractionResult("unavailable")
