import pytest

from backend.app.reality.claim_conflict import ClaimConflict, ClaimConflictResult
from backend.app.reality.claim_conflict_detector import ClaimConflictDetector
from backend.app.reality.claim_conflict_normalizer import ClaimConflictResultNormalizer
from backend.app.reality.claim_extraction import ClaimExtractionResult, EvidenceClaim


def test_step156_accepts_canonical_claim_conflict_result():
    conflict = ClaimConflict(
        claim_a="available",
        claim_b="not available",
        source_refs_a=("https://a.example",),
        source_refs_b=("https://b.example",),
    )
    result = ClaimConflictResult.usable_result((conflict,), claim_count=2)

    assert ClaimConflictResult.validate(result) is result


def test_step156_normalizes_mapping():
    result = ClaimConflictResultNormalizer.normalize(
        {
            "status": "usable",
            "conflicts": [
                {
                    "claim_a": "available",
                    "claim_b": "not available",
                    "source_refs_a": ["https://a.example"],
                    "source_refs_b": ["https://b.example"],
                    "conflict_method": "explicit_negation_pair",
                }
            ],
            "conflict_count": 1,
            "claim_count": 2,
            "detection_executed": True,
            "reason": None,
        }
    )

    assert result.status == "usable"
    assert len(result.conflicts) == 1
    assert result.conflict_count == 1


def test_step156_rejects_missing_required_result_field():
    with pytest.raises(ValueError, match="missing required fields"):
        ClaimConflictResult.validate(
            {
                "status": "usable",
                "conflicts": [],
                "claim_count": 2,
            }
        )


def test_step156_rejects_malformed_nested_conflict():
    with pytest.raises(ValueError, match="claim conflict is missing required fields"):
        ClaimConflictResultNormalizer.normalize(
            {
                "status": "usable",
                "conflicts": [{"claim_a": "available"}],
                "claim_count": 2,
                "conflict_count": 1,
                "detection_executed": True,
                "reason": None,
            }
        )


def test_step156_rejects_conflict_count_mismatch():
    with pytest.raises(ValueError, match="conflict_count must match conflicts"):
        ClaimConflictResultNormalizer.normalize(
            {
                "status": "empty",
                "conflicts": [],
                "claim_count": 2,
                "conflict_count": 1,
                "detection_executed": True,
                "reason": None,
            }
        )


def test_step156_detector_returns_canonical_validated_result():
    claim_result = ClaimExtractionResult.usable_result(
        (
            EvidenceClaim("available", ("https://a.example",)),
            EvidenceClaim("not available", ("https://b.example",)),
        ),
        source_count=2,
    )

    result = ClaimConflictDetector().detect_result(claim_result)

    assert isinstance(result, ClaimConflictResult)
    assert result.status == "usable"
    assert result.conflict_count == 1
    assert result.conflicts[0].conflict_method == "explicit_negation_pair"
