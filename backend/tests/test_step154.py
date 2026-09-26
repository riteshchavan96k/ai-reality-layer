import pytest

from backend.app.reality.claim_extraction import ClaimExtractionResult, EvidenceClaim
from backend.app.reality.claim_extraction_normalizer import ClaimExtractionResultNormalizer
from backend.app.reality.claim_extractor import EvidenceClaimExtractor


def test_step154_accepts_canonical_claim_extraction_result():
    claim = EvidenceClaim(text="The system is operational.", source_refs=("https://example.com",))
    result = ClaimExtractionResult.usable_result((claim,), source_count=1)

    assert ClaimExtractionResult.validate(result) is result


def test_step154_normalizes_compatible_mapping():
    result = ClaimExtractionResultNormalizer.normalize(
        {
            "status": "usable",
            "claims": [
                {
                    "text": "The system is operational.",
                    "source_refs": ["https://example.com"],
                    "extraction_method": "deterministic_sentence_split",
                }
            ],
            "claim_count": 1,
            "source_count": 1,
            "extraction_executed": True,
            "reason": None,
        }
    )

    assert result.status == "usable"
    assert len(result.claims) == 1
    assert result.claims[0].text == "The system is operational."
    assert result.source_count == 1


def test_step154_rejects_missing_required_field():
    with pytest.raises(ValueError, match="missing required fields"):
        ClaimExtractionResult.validate(
            {
                "status": "usable",
                "claims": [],
                "source_count": 1,
            }
        )


def test_step154_rejects_malformed_nested_claim():
    with pytest.raises(ValueError, match="claim is missing required fields"):
        ClaimExtractionResultNormalizer.normalize(
            {
                "status": "usable",
                "claims": [{"text": "The system is operational."}],
                "source_count": 1,
                "extraction_executed": True,
                "reason": None,
            }
        )


def test_step154_rejects_status_claim_inconsistency():
    with pytest.raises(ValueError, match="usable claim extraction requires at least one claim"):
        ClaimExtractionResultNormalizer.normalize(
            {
                "status": "usable",
                "claims": [],
                "source_count": 1,
                "extraction_executed": True,
                "reason": None,
            }
        )


def test_step154_extractor_returns_canonical_validated_result():
    result = EvidenceClaimExtractor().extract_result(
        {
            "status": "usable",
            "sources": [{"uri": "https://example.com"}],
            "content": "The system is operational.",
        }
    )

    assert isinstance(result, ClaimExtractionResult)
    assert result.status == "usable"
    assert result.claims[0].source_refs == ("https://example.com",)
