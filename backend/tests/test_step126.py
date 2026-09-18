import pytest

from backend.app.reality.claim_evidence_linker import ClaimEvidenceLinker
from backend.app.reality.claim_evidence_linking import ClaimEvidenceLink, ClaimEvidenceLinkingResult
from backend.app.reality.claim_extraction import ClaimExtractionResult, EvidenceClaim


def usable_claim_result(*claims: EvidenceClaim) -> ClaimExtractionResult:
    return ClaimExtractionResult.usable_result(tuple(claims), source_count=1)


def test_link_contract_is_immutable_and_serializable():
    link = ClaimEvidenceLink("A statement.", "https://example.com/a")
    assert link.to_dict() == {"claim_text": "A statement.", "source_ref": "https://example.com/a", "relationship": "derived_from", "linking_method": "source_ref_intersection"}
    with pytest.raises(Exception):
        link.source_ref = "changed"


def test_linker_matches_claim_source_refs_to_known_evidence_sources():
    result = ClaimEvidenceLinker().link_result(usable_claim_result(EvidenceClaim("A statement.", ("https://example.com/a",))), {"status": "usable", "sources": [{"title": "A", "uri": "https://example.com/a"}], "content": "A statement."})
    assert isinstance(result, ClaimEvidenceLinkingResult)
    assert result.status == "usable"
    assert result.links[0].claim_text == "A statement."
    assert result.links[0].source_ref == "https://example.com/a"
    assert result.linked_claim_count == 1


def test_linker_does_not_invent_links_for_unknown_source_refs():
    result = ClaimEvidenceLinker().link_result(usable_claim_result(EvidenceClaim("A statement.", ("https://unknown.example",))), {"status": "usable", "sources": [{"title": "A", "uri": "https://example.com/a"}], "content": "A statement."})
    assert result.status == "empty"
    assert result.links == ()
    assert result.unlinked_claim_count == 1


def test_linker_deduplicates_repeated_claim_source_pairs():
    result = ClaimEvidenceLinker().link_result(usable_claim_result(EvidenceClaim("A statement.", ("https://example.com/a", "https://example.com/a"))), {"status": "usable", "sources": [{"title": "A", "uri": "https://example.com/a"}], "content": "A statement."})
    assert len(result.links) == 1


def test_unavailable_claim_extraction_stays_unavailable():
    claim_result = ClaimExtractionResult.unavailable_result("evidence_not_usable")
    result = ClaimEvidenceLinker().link_result(claim_result, {"status": "invalid_evidence", "sources": [], "content": None, "reason": "evidence_not_usable"})
    assert result.status == "unavailable"
    assert result.reason == "evidence_not_usable"
    assert result.links == ()


def test_empty_claim_extraction_returns_empty_linking_result():
    result = ClaimEvidenceLinker().link_result(ClaimExtractionResult.empty_result(source_count=1), {"status": "usable", "sources": [{"title": "A", "uri": "https://example.com/a"}], "content": ""})
    assert result.status == "empty"
    assert result.links == ()


def test_dictionary_claim_result_api_is_supported():
    result = ClaimEvidenceLinker().link({"status": "usable", "claims": [{"text": "A statement.", "source_refs": ["https://example.com/a"], "extraction_method": "deterministic_sentence_split"}], "source_count": 1, "extraction_executed": True, "reason": None}, {"status": "usable", "sources": [{"title": "A", "uri": "https://example.com/a"}], "content": "A statement."})
    assert result["status"] == "usable"
    assert result["link_count"] == 1


def test_link_result_rejects_inconsistent_states():
    link = ClaimEvidenceLink("A statement.", "https://example.com/a")
    with pytest.raises(ValueError, match="usable claim-evidence linking requires"):
        ClaimEvidenceLinkingResult("usable", claim_count=1)
    with pytest.raises(ValueError, match="empty claim-evidence linking cannot"):
        ClaimEvidenceLinkingResult("empty", links=(link,), claim_count=1, linked_claim_count=1)
    with pytest.raises(ValueError, match="requires a reason"):
        ClaimEvidenceLinkingResult("unavailable")