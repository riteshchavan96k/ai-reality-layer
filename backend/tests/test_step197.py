"""Step 197 — canonical claim-evidence linked-claim count integrity."""

import pytest

from backend.app.reality.claim_evidence_linker import ClaimEvidenceLinker
from backend.app.reality.claim_evidence_linking import (
    ClaimEvidenceLink,
    ClaimEvidenceLinkingResult,
)
from backend.app.reality.claim_evidence_linking_normalizer import (
    ClaimEvidenceLinkingResultNormalizer,
)
from backend.app.reality.claim_extraction import ClaimExtractionResult, EvidenceClaim
from backend.app.reality.confidence_signal_aggregator import (
    RealityConfidenceSignalAggregator,
)


CLAIM_A = "The service is operational."
CLAIM_B = "The service is available."
SOURCE_A = "https://a.example"
SOURCE_B = "https://b.example"


def _link(claim_text: str = CLAIM_A, source_ref: str = SOURCE_A) -> ClaimEvidenceLink:
    return ClaimEvidenceLink(
        claim_text=claim_text,
        source_ref=source_ref,
    )


def _usable_mapping(*, linked_claim_count: object) -> dict:
    return {
        "status": "usable",
        "links": [_link().to_dict()],
        "claim_count": 1,
        "linked_claim_count": linked_claim_count,
        "source_count": 1,
        "linking_executed": True,
        "reason": None,
    }


def test_direct_result_rejects_overstated_linked_claim_count():
    with pytest.raises(
        ValueError,
        match="linked_claim_count must match distinct linked claims",
    ):
        ClaimEvidenceLinkingResult(
            status="usable",
            links=(_link(),),
            claim_count=2,
            linked_claim_count=2,
            source_count=1,
        )


def test_direct_result_rejects_understated_linked_claim_count():
    with pytest.raises(
        ValueError,
        match="linked_claim_count must match distinct linked claims",
    ):
        ClaimEvidenceLinkingResult(
            status="usable",
            links=(_link(),),
            claim_count=1,
            linked_claim_count=0,
            source_count=1,
        )


def test_empty_result_rejects_inflated_linked_claim_count():
    with pytest.raises(
        ValueError,
        match="linked_claim_count must match distinct linked claims",
    ):
        ClaimEvidenceLinkingResult(
            status="empty",
            links=(),
            claim_count=1,
            linked_claim_count=1,
            source_count=1,
        )


def test_mapping_rejects_overstated_linked_claim_count():
    raw = {
        "status": "usable",
        "links": [_link().to_dict()],
        "claim_count": 2,
        "linked_claim_count": 2,
        "source_count": 1,
        "linking_executed": True,
        "reason": None,
    }

    with pytest.raises(
        ValueError,
        match="linked_claim_count must match distinct linked claims",
    ):
        ClaimEvidenceLinkingResult.validate(raw)


def test_normalizer_rejects_understated_linked_claim_count():
    with pytest.raises(
        ValueError,
        match="linked_claim_count must match distinct linked claims",
    ):
        ClaimEvidenceLinkingResultNormalizer.normalize(
            _usable_mapping(linked_claim_count=0)
        )


def test_multiple_links_for_same_claim_count_as_one_linked_claim():
    result = ClaimEvidenceLinkingResult(
        status="usable",
        links=(
            _link(CLAIM_A, SOURCE_A),
            _link(CLAIM_A, SOURCE_B),
        ),
        claim_count=1,
        linked_claim_count=1,
        source_count=2,
    )

    assert result.linked_claim_count == 1
    assert len(result.links) == 2
    assert result.unlinked_claim_count == 0


def test_case_variants_of_same_claim_count_as_one_linked_claim():
    result = ClaimEvidenceLinkingResult(
        status="usable",
        links=(
            _link(CLAIM_A, SOURCE_A),
            _link(CLAIM_A.upper(), SOURCE_B),
        ),
        claim_count=1,
        linked_claim_count=1,
        source_count=2,
    )

    assert result.linked_claim_count == 1


def test_two_distinct_linked_claims_require_count_two():
    result = ClaimEvidenceLinkingResult(
        status="usable",
        links=(
            _link(CLAIM_A, SOURCE_A),
            _link(CLAIM_B, SOURCE_B),
        ),
        claim_count=2,
        linked_claim_count=2,
        source_count=2,
    )

    assert result.linked_claim_count == 2
    assert result.unlinked_claim_count == 0


def test_two_distinct_linked_claims_reject_count_one():
    with pytest.raises(
        ValueError,
        match="linked_claim_count must match distinct linked claims",
    ):
        ClaimEvidenceLinkingResult(
            status="usable",
            links=(
                _link(CLAIM_A, SOURCE_A),
                _link(CLAIM_B, SOURCE_B),
            ),
            claim_count=2,
            linked_claim_count=1,
            source_count=2,
        )


def test_usable_helper_preserves_distinct_claim_count_semantics():
    result = ClaimEvidenceLinkingResult.usable_result(
        (
            _link(CLAIM_A, SOURCE_A),
            _link(CLAIM_A, SOURCE_B),
            _link(CLAIM_B, SOURCE_B),
        ),
        claim_count=2,
        source_count=2,
    )

    assert result.linked_claim_count == 2
    assert result.unlinked_claim_count == 0


def test_empty_helper_preserves_zero_linked_claim_count():
    result = ClaimEvidenceLinkingResult.empty_result(
        claim_count=1,
        source_count=1,
    )

    assert result.status == "empty"
    assert result.links == ()
    assert result.linked_claim_count == 0
    assert result.unlinked_claim_count == 1


def test_production_linker_returns_count_matching_actual_distinct_links():
    claims = ClaimExtractionResult.usable_result(
        (
            EvidenceClaim(CLAIM_A, (SOURCE_A, SOURCE_B)),
            EvidenceClaim(CLAIM_B, (SOURCE_B,)),
        ),
        source_count=2,
    )
    result = ClaimEvidenceLinker().link_result(
        claims,
        {
            "status": "usable",
            "sources": [
                {"uri": SOURCE_A},
                {"uri": SOURCE_B},
            ],
        },
    )

    actual = len({link.claim_text.casefold() for link in result.links})
    assert result.status == "usable"
    assert result.linked_claim_count == actual == 2


def test_valid_full_coverage_remains_supported_by_confidence():
    linking = ClaimEvidenceLinkingResult.usable_result(
        (
            _link(CLAIM_A, SOURCE_A),
            _link(CLAIM_B, SOURCE_B),
        ),
        claim_count=2,
        source_count=2,
    ).to_dict()

    confidence = RealityConfidenceSignalAggregator().aggregate_result(
        evidence_quality={"status": "usable"},
        linking=linking,
        freshness={
            "status": "usable",
            "stale_count": 0,
            "unknown_count": 0,
        },
        conflicts={
            "status": "empty",
            "conflict_count": 0,
            "detection_executed": True,
        },
    )

    assert linking["linked_claim_count"] == 2
    assert confidence.claim_coverage == 1.0
    assert confidence.status == "supported"


def test_canonical_result_blocks_false_full_coverage_before_confidence():
    with pytest.raises(
        ValueError,
        match="linked_claim_count must match distinct linked claims",
    ):
        ClaimEvidenceLinkingResult(
            status="usable",
            links=(_link(CLAIM_A, SOURCE_A),),
            claim_count=2,
            linked_claim_count=2,
            source_count=1,
        )


def test_canonical_empty_result_blocks_false_full_coverage_before_confidence():
    with pytest.raises(
        ValueError,
        match="linked_claim_count must match distinct linked claims",
    ):
        ClaimEvidenceLinkingResult(
            status="empty",
            links=(),
            claim_count=1,
            linked_claim_count=1,
            source_count=1,
        )


def test_existing_overflow_guard_remains_intact():
    with pytest.raises(
        ValueError,
        match="linked_claim_count cannot exceed claim_count",
    ):
        ClaimEvidenceLinkingResult(
            status="usable",
            links=(_link(),),
            claim_count=1,
            linked_claim_count=2,
            source_count=1,
        )
