"""Step 216: structural identity for candidate conflicts and their source refs.

The deterministic detector already deduplicates unordered, case-insensitive
pairs. Direct typed/mapping result creation must not inflate conflict counts
or reintroduce noncanonical source provenance references.
"""

import pytest

from backend.app.orchestrator.orchestrator import build_reality_state_from_evidence
from backend.app.reality.claim_conflict import ClaimConflict, ClaimConflictResult
from backend.app.reality.claim_conflict_detector import ClaimConflictDetector
from backend.app.reality.claim_conflict_normalizer import (
    ClaimConflictResultNormalizer,
)
from backend.app.reality.claim_extraction import ClaimExtractionResult, EvidenceClaim
from backend.app.reality.confidence_signal_aggregator import (
    RealityConfidenceSignalAggregator,
)


A = "https://example.test/a"
B = "https://example.test/b"
C = "https://example.test/c"
POSITIVE = "Service available."
NEGATIVE = "Not service available."


def _conflict(a=POSITIVE, b=NEGATIVE, refs_a=(A,), refs_b=(B,)):
    return ClaimConflict(
        claim_a=a, claim_b=b,
        source_refs_a=refs_a, source_refs_b=refs_b,
    )


def _mapping(conflicts, claim_count=2):
    return {
        "status": "usable",
        "conflicts": [item.to_dict() for item in conflicts],
        "claim_count": claim_count,
        "conflict_count": len(conflicts),
        "detection_executed": True,
        "reason": None,
    }


@pytest.mark.parametrize("ref", [
    " " + A, A + " ", "\t" + A, A + "\n"
])
@pytest.mark.parametrize("which", ["source_refs_a", "source_refs_b"])
def test_direct_conflict_rejects_noncanonical_padded_ref(ref, which):
    kwargs = {"refs_a" if which == "source_refs_a" else "refs_b": (ref,)}
    with pytest.raises(ValueError, match="must contain canonical source references"):
        _conflict(**kwargs)


@pytest.mark.parametrize("which", ["source_refs_a", "source_refs_b"])
def test_mapping_and_normalizer_reject_padded_ref(which):
    mapping = _mapping((_conflict(),))
    mapping["conflicts"][0][which] = [" " + A + " "]
    with pytest.raises(ValueError, match="must contain canonical source references"):
        ClaimConflictResult.validate(mapping)
    with pytest.raises(ValueError, match="must contain canonical source references"):
        ClaimConflictResultNormalizer.normalize(mapping)


@pytest.mark.parametrize("second", [
    _conflict(),
    _conflict(a=NEGATIVE, b=POSITIVE, refs_a=(B,), refs_b=(A,)),
    _conflict(a=POSITIVE.lower(), b=NEGATIVE.upper()),
    _conflict(refs_a=(C,), refs_b=(A,)),
])
def test_duplicate_pair_rejected_regardless_of_orientation_case_or_provenance(second):
    with pytest.raises(ValueError, match="unique claim pairs"):
        ClaimConflictResult.usable_result(
            (_conflict(), second), claim_count=2
        )


def test_direct_constructor_rejects_reversed_pair_with_matching_counts():
    with pytest.raises(ValueError, match="unique claim pairs"):
        ClaimConflictResult(
            status="usable",
            conflicts=(
                _conflict(),
                _conflict(a=NEGATIVE, b=POSITIVE, refs_a=(B,), refs_b=(A,)),
            ),
            conflict_count=2,
            claim_count=2,
        )


@pytest.mark.parametrize("nested_typed", [False, True])
def test_mapping_and_normalizer_reject_repeated_unordered_pair(nested_typed):
    first = _conflict()
    second = _conflict(a=NEGATIVE.upper(), b=POSITIVE.lower())
    mapping = _mapping((first, second))
    if nested_typed:
        mapping["conflicts"] = [first, second]
    with pytest.raises(ValueError, match="unique claim pairs"):
        ClaimConflictResult.validate(mapping)
    with pytest.raises(ValueError, match="unique claim pairs"):
        ClaimConflictResultNormalizer.normalize(mapping)


def test_two_independent_conflict_pairs_remain_valid_and_roundtrip():
    conflicts = (
        _conflict(),
        _conflict(a="Feature B enabled.", b="Not feature B enabled.", refs_a=(A,), refs_b=(C,)),
    )
    result = ClaimConflictResult.usable_result(conflicts, claim_count=4)
    assert result.status == "usable"
    assert result.conflict_count == 2
    assert ClaimConflictResult.validate(result.to_dict()) == result
    assert ClaimConflictResultNormalizer.normalize(result.to_dict()) == result


def test_source_lineage_remains_distinct_and_url_not_rewritten():
    record = _conflict(refs_a=(A, A + "/"), refs_b=(B, C))
    result = ClaimConflictResult.usable_result((record,), claim_count=2)
    assert result.conflicts[0].source_refs_a == (A, A + "/")
    assert result.conflicts[0].source_refs_b == (B, C)


def test_empty_source_refs_remain_legacy_compatible():
    result = ClaimConflictResult.usable_result(
        (_conflict(refs_a=(), refs_b=()),), claim_count=2
    )
    assert result.conflict_count == 1
    assert result.conflicts[0].source_refs_a == ()


def test_empty_and_unavailable_result_states_remain_unchanged():
    empty = ClaimConflictResult.empty_result(claim_count=2)
    unavailable = ClaimConflictResult.unavailable_result(
        "claim_extraction_unavailable", claim_count=2
    )
    assert empty.status == "empty" and empty.conflicts == ()
    assert unavailable.status == "unavailable" and unavailable.conflicts == ()
    assert ClaimConflictResult.validate(empty.to_dict()) == empty
    assert ClaimConflictResult.validate(unavailable.to_dict()) == unavailable


def test_existing_detector_produces_one_conflict_with_source_refs():
    claims = ClaimExtractionResult.usable_result(
        (
            EvidenceClaim(POSITIVE, (A,)),
            EvidenceClaim(NEGATIVE, (B,)),
        ),
        source_count=2,
    )
    result = ClaimConflictDetector().detect_result(claims)
    assert result.conflict_count == 1
    assert result.conflicts[0].claim_a == POSITIVE
    assert result.conflicts[0].claim_b == NEGATIVE
    assert result.conflicts[0].source_refs_a == (A,)
    assert result.conflicts[0].source_refs_b == (B,)


def test_detector_case_aliases_do_not_create_repeated_conflicts():
    claims = ClaimExtractionResult.usable_result(
        (
            EvidenceClaim(POSITIVE, (A,)),
            EvidenceClaim(NEGATIVE, (B,)),
            EvidenceClaim(POSITIVE.upper(), (C,)),
            EvidenceClaim(NEGATIVE.lower(), (C,)),
        ),
        source_count=3,
    )
    result = ClaimConflictDetector().detect_result(claims)
    assert result.conflict_count == 1
    assert len(result.conflicts) == 1


def test_conflict_count_is_exact_for_confidence_aggregator():
    conflicts = ClaimConflictResult.usable_result(
        (_conflict(),), claim_count=2
    )
    signals = RealityConfidenceSignalAggregator().aggregate_result(
        evidence_quality={"status": "usable"},
        linking={"status": "usable", "claim_count": 2, "linked_claim_count": 2},
        freshness={"status": "usable", "stale_count": 0, "unknown_count": 0},
        conflicts=conflicts.to_dict(),
    )
    assert signals.status == "uncertain"
    assert signals.conflict_count == 1
    assert "candidate_conflicts_present" in signals.signals


def test_end_to_end_submitted_reality_state_preserves_one_conflict_and_lineage():
    state = build_reality_state_from_evidence(
        "What is the current service status?",
        [
            {"uri": A, "content": POSITIVE},
            {"uri": B, "content": NEGATIVE},
        ],
    )
    assert state["claims"]["status"] == "usable"
    assert state["claims"]["claim_count"] == 2
    conflicts = state["conflicts"]
    assert conflicts["status"] == "usable"
    assert conflicts["conflict_count"] == len(conflicts["conflicts"]) == 1
    pair = conflicts["conflicts"][0]
    assert pair["claim_a"] == POSITIVE
    assert pair["claim_b"] == NEGATIVE
    assert pair["source_refs_a"] == [A]
    assert pair["source_refs_b"] == [B]
    assert {
        link["source_ref"] for link in state["claim_evidence_linking"]["links"]
    } == {A, B}
    assert state["confidence_signals"]["status"] == "uncertain"
