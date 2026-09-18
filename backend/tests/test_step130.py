from backend.app.reality.claim_conflict import ClaimConflict, ClaimConflictResult
from backend.app.reality.claim_conflict_detector import ClaimConflictDetector
from backend.app.reality.claim_extraction import ClaimExtractionResult, EvidenceClaim
import pytest


def claims(*texts):
    return ClaimExtractionResult.usable_result(tuple(EvidenceClaim(t, ("https://a.example",)) for t in texts), 1)


def test_explicit_negation_pair_is_detected():
    result = ClaimConflictDetector().detect_result(claims("available", "not available"))
    assert result.status == "usable"
    assert result.conflict_count == 1
    assert result.conflicts[0].conflict_method == "explicit_negation_pair"


def test_non_conflicting_claims_remain_empty():
    result = ClaimConflictDetector().detect_result(claims("available", "unavailable"))
    assert result.status == "empty"


def test_unavailable_and_empty_extraction_propagate():
    detector = ClaimConflictDetector()
    assert detector.detect_result(ClaimExtractionResult.unavailable_result("extractor_failed")).status == "unavailable"
    assert detector.detect_result(ClaimExtractionResult.empty_result()).status == "empty"


def test_dict_api_and_deterministic_serialization():
    result = ClaimConflictDetector().detect(claims("ready", "not ready"))
    assert result["conflict_count"] == 1
    assert result == ClaimConflictDetector().detect(claims("ready", "not ready"))


def test_conflict_contract_is_immutable_and_rejects_invalid_states():
    item = ClaimConflict("ready", "not ready", ("a",), ("b",))
    assert item.to_dict()["source_refs_a"] == ["a"]
    with pytest.raises(Exception):
        item.claim_a = "changed"
    with pytest.raises(ValueError, match="usable conflict result requires"):
        ClaimConflictResult("usable")
