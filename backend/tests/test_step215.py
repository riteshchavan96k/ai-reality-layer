"""Step 215 — canonical claim/evidence relationship identity integrity.

Steps 212–214 established unique provenance and temporal source identities;
the canonical link contract must uphold the same source identity and forbid
the duplicate (case-insensitive claim, source) pairs filtered by the linker.
"""

import hashlib

import pytest

from backend.app.orchestrator.orchestrator import build_reality_state_from_evidence
from backend.app.reality.claim_evidence_linker import ClaimEvidenceLinker
from backend.app.reality.claim_evidence_linking import (
    ClaimEvidenceLink,
    ClaimEvidenceLinkingResult,
)
from backend.app.reality.claim_evidence_linking_normalizer import (
    ClaimEvidenceLinkingResultNormalizer,
)
from backend.app.reality.claim_extractor import EvidenceClaimExtractor
from backend.app.reality.source_provenance_builder import SourceProvenanceBuilder


A = "https://example.test/official-a"
B = "https://example.test/official-b"
CLAIM = "Company X launched Feature A."
OTHER = "Company Y announced Feature B."


def _link(text=CLAIM, ref=A, method="source_ref_intersection"):
    return ClaimEvidenceLink(
        claim_text=text, source_ref=ref, linking_method=method,
    )


def _mapping(links, *, claim_count=1, source_count=2, linked_claim_count=1):
    return {
        "status": "usable",
        "links": [link.to_dict() for link in links],
        "claim_count": claim_count,
        "linked_claim_count": linked_claim_count,
        "source_count": source_count,
        "linking_executed": True,
        "reason": None,
    }


@pytest.mark.parametrize("ref", [
    " " + A,
    A + " ",
    "\t" + A + "\n",
    "\n" + A,
])
def test_direct_link_rejects_noncanonical_padded_source_ref(ref):
    with pytest.raises(ValueError, match="source_ref must be a canonical source reference"):
        _link(ref=ref)


@pytest.mark.parametrize("ref", [
    " " + A,
    A + " ",
])
def test_mapping_link_rejects_noncanonical_padded_ref(ref):
    mapping = _mapping((_link(),))
    mapping["links"][0]["source_ref"] = ref
    with pytest.raises(ValueError, match="source_ref must be a canonical source reference"):
        ClaimEvidenceLinkingResult.validate(mapping)
    with pytest.raises(ValueError, match="source_ref must be a canonical source reference"):
        ClaimEvidenceLinkingResultNormalizer.normalize(mapping)


@pytest.mark.parametrize("second", [
    _link(),
    _link(text=CLAIM.lower()),
    _link(text=CLAIM.upper()),
    _link(method="trusted_alternative_link_method"),
])
def test_duplicate_claim_source_relationship_rejected_regardless_of_case_or_method(second):
    with pytest.raises(ValueError, match="unique claim-source pairs"):
        ClaimEvidenceLinkingResult.usable_result(
            (_link(), second), claim_count=1, source_count=2
        )


def test_explicit_constructor_rejects_repeated_claim_source_relationship():
    with pytest.raises(ValueError, match="unique claim-source pairs"):
        ClaimEvidenceLinkingResult(
            status="usable",
            links=(_link(), _link(text=CLAIM.lower())),
            claim_count=1,
            linked_claim_count=1,
            source_count=1,
        )


@pytest.mark.parametrize("typed", [True, False])
def test_mapping_validation_and_normalizer_reject_duplicate_pairs(typed):
    first, second = _link(), _link(text=CLAIM.lower())
    mapping = _mapping((first, second))
    if typed:
        mapping["links"] = [first, second]
    with pytest.raises(ValueError, match="unique claim-source pairs"):
        ClaimEvidenceLinkingResult.validate(mapping)
    with pytest.raises(ValueError, match="unique claim-source pairs"):
        ClaimEvidenceLinkingResultNormalizer.normalize(mapping)


def test_same_claim_from_two_sources_remains_two_distinct_valid_links():
    links = (_link(ref=A), _link(ref=B))
    result = ClaimEvidenceLinkingResult.usable_result(
        links, claim_count=1, source_count=2
    )
    assert result.status == "usable"
    assert result.linked_claim_count == 1
    assert result.unlinked_claim_count == 0
    assert len(result.links) == 2
    assert result.to_dict()["link_count"] == 2
    assert ClaimEvidenceLinkingResult.validate(result.to_dict()) == result
    assert ClaimEvidenceLinkingResultNormalizer.normalize(result.to_dict()) == result


def test_multiple_different_claims_can_link_to_one_source():
    result = ClaimEvidenceLinkingResult.usable_result(
        (_link(text=CLAIM, ref=A), _link(text=OTHER, ref=A)),
        claim_count=2, source_count=1,
    )
    assert result.linked_claim_count == 2
    assert len(result.links) == 2
    assert result.unlinked_claim_count == 0


def test_case_insensitive_claim_identity_is_source_scoped():
    result = ClaimEvidenceLinkingResult.usable_result(
        (_link(text=CLAIM, ref=A), _link(text=CLAIM.upper(), ref=B)),
        claim_count=1, source_count=2,
    )
    assert result.linked_claim_count == 1
    assert result.to_dict()["link_count"] == 2


def test_canonical_source_ref_remains_exact_not_url_rewritten():
    ref = A + "/"
    result = ClaimEvidenceLinkingResult.usable_result(
        (_link(ref=A), _link(ref=ref)),
        claim_count=1, source_count=2,
    )
    assert [link.source_ref for link in result.links] == [A, ref]


def test_default_linker_already_deduplicates_claims_and_trims_known_sources():
    evidence = {
        "status": "usable",
        "sources": [
            {"uri": " " + A + " ", "content": CLAIM},
            {"uri": "\t" + B, "content": CLAIM},
        ],
        "content": CLAIM + "\n\n" + CLAIM,
    }
    claims = EvidenceClaimExtractor().extract_result(evidence)
    result = ClaimEvidenceLinker().link_result(claims, evidence)
    assert result.status == "usable"
    assert [(link.claim_text, link.source_ref) for link in result.links] == [
        (CLAIM, A), (CLAIM, B),
    ]
    assert result.linked_claim_count == 1
    assert result.to_dict()["link_count"] == 2
    assert result == ClaimEvidenceLinkingResult.validate(result.to_dict())


def test_provenance_refs_and_link_refs_match_after_canonicalization():
    evidence = {
        "status": "usable",
        "sources": [{"uri": " " + A + " "}, {"uri": B + " "}],
        "content": CLAIM,
    }
    provenance = SourceProvenanceBuilder().build_result(evidence)
    claims = EvidenceClaimExtractor().extract_result(evidence)
    linking = ClaimEvidenceLinker().link_result(claims, evidence)
    assert linking.status == "empty" or linking.status == "usable"
    if linking.status == "usable":
        assert {link.source_ref for link in linking.links} <= {
            source.source_ref for source in provenance.sources
        }


def test_empty_and_unavailable_link_states_remain_compatible():
    empty = ClaimEvidenceLinkingResult.empty_result(claim_count=1, source_count=2)
    unavailable = ClaimEvidenceLinkingResult.unavailable_result(
        "claim_extraction_unavailable", claim_count=1, source_count=2
    )
    assert empty.status == "empty" and empty.links == ()
    assert unavailable.status == "unavailable" and unavailable.links == ()
    assert ClaimEvidenceLinkingResult.validate(empty.to_dict()) == empty
    assert ClaimEvidenceLinkingResult.validate(unavailable.to_dict()) == unavailable


def test_end_to_end_reality_state_preserves_distinct_claim_source_links():
    state = build_reality_state_from_evidence(
        "What did Company X launch?",
        [
            {"uri": A, "content": CLAIM},
            {"uri": B, "content": CLAIM},
        ],
        entity="Company X",
    )
    assert state["claims"]["status"] == "usable"
    assert state["claims"]["claim_count"] == 1
    assert state["claims"]["claims"][0]["source_refs"] == [A, B]
    linking = state["claim_evidence_linking"]
    assert linking["status"] == "usable"
    assert linking["link_count"] == 2
    assert linking["linked_claim_count"] == 1
    assert {link["source_ref"] for link in linking["links"]} == {A, B}
    assert {(link["claim_text"].casefold(), link["source_ref"]) for link in linking["links"]} == {
        (CLAIM.casefold(), A),
        (CLAIM.casefold(), B),
    }
    provenance = state["source_provenance"]
    assert {link["source_ref"] for link in linking["links"]} == {
        source["source_ref"] for source in provenance["sources"]
    }
    assert {source["source_id"] for source in provenance["sources"]} == {
        hashlib.sha256(uri.encode("utf-8")).hexdigest() for uri in (A, B)
    }
