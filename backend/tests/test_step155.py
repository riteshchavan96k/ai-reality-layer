import pytest

from backend.app.reality.claim_evidence_linking import ClaimEvidenceLink, ClaimEvidenceLinkingResult
from backend.app.reality.claim_evidence_linking_normalizer import ClaimEvidenceLinkingResultNormalizer


def test_step155_accepts_canonical_claim_evidence_linking_result():
    link = ClaimEvidenceLink(
        claim_text="The system is operational.",
        source_ref="https://example.com",
    )
    result = ClaimEvidenceLinkingResult.usable_result(
        (link,),
        claim_count=1,
        source_count=1,
    )

    assert ClaimEvidenceLinkingResult.validate(result) is result


def test_step155_normalizes_mapping():
    result = ClaimEvidenceLinkingResultNormalizer.normalize(
        {
            "status": "usable",
            "links": [
                {
                    "claim_text": "The system is operational.",
                    "source_ref": "https://example.com",
                    "relationship": "derived_from",
                    "linking_method": "source_ref_intersection",
                }
            ],
            "link_count": 1,
            "claim_count": 1,
            "linked_claim_count": 1,
            "unlinked_claim_count": 0,
            "source_count": 1,
            "linking_executed": True,
            "reason": None,
        }
    )

    assert result.status == "usable"
    assert len(result.links) == 1
    assert result.linked_claim_count == 1


def test_step155_rejects_missing_required_result_field():
    with pytest.raises(ValueError, match="missing required fields"):
        ClaimEvidenceLinkingResult.validate(
            {
                "status": "usable",
                "links": [],
                "claim_count": 1,
                "linked_claim_count": 0,
                "source_count": 1,
            }
        )


def test_step155_rejects_malformed_nested_link():
    with pytest.raises(ValueError, match="link is missing required fields"):
        ClaimEvidenceLinkingResultNormalizer.normalize(
            {
                "status": "usable",
                "links": [{"claim_text": "The system is operational."}],
                "claim_count": 1,
                "linked_claim_count": 1,
                "source_count": 1,
                "linking_executed": True,
                "reason": None,
            }
        )


def test_step155_rejects_linked_claim_count_overflow():
    with pytest.raises(ValueError, match="cannot exceed claim_count"):
        ClaimEvidenceLinkingResultNormalizer.normalize(
            {
                "status": "empty",
                "links": [],
                "claim_count": 1,
                "linked_claim_count": 2,
                "source_count": 1,
                "linking_executed": True,
                "reason": None,
            }
        )
