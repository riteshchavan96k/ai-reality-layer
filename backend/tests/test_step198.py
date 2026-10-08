"""Step 198 — canonical claim-evidence linking execution-state integrity."""

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


CLAIM = "The service is operational."
SOURCE = "https://example.com"


def _link() -> ClaimEvidenceLink:
    return ClaimEvidenceLink(
        claim_text=CLAIM,
        source_ref=SOURCE,
    )


def _usable_mapping(*, linking_executed: object) -> dict:
    return {
        "status": "usable",
        "links": [_link().to_dict()],
        "claim_count": 1,
        "linked_claim_count": 1,
        "source_count": 1,
        "linking_executed": linking_executed,
        "reason": None,
    }


def test_usable_result_rejects_false_execution_flag():
    with pytest.raises(
        ValueError,
        match="usable claim-evidence linking requires linking_executed to be True",
    ):
        ClaimEvidenceLinkingResult(
            status="usable",
            links=(_link(),),
            claim_count=1,
            linked_claim_count=1,
            source_count=1,
            linking_executed=False,
        )


def test_mapping_rejects_usable_false_execution_flag():
    with pytest.raises(
        ValueError,
        match="usable claim-evidence linking requires linking_executed to be True",
    ):
        ClaimEvidenceLinkingResult.validate(
            _usable_mapping(linking_executed=False)
        )


def test_normalizer_rejects_usable_false_execution_flag():
    with pytest.raises(
        ValueError,
        match="usable claim-evidence linking requires linking_executed to be True",
    ):
        ClaimEvidenceLinkingResultNormalizer.normalize(
            _usable_mapping(linking_executed=False)
        )


def test_usable_true_execution_flag_remains_valid():
    result = ClaimEvidenceLinkingResult.validate(
        _usable_mapping(linking_executed=True)
    )

    assert result.status == "usable"
    assert result.linking_executed is True
    assert result.linked_claim_count == 1


def test_non_boolean_execution_flag_remains_rejected():
    with pytest.raises(
        ValueError,
        match="linking_executed must be a boolean",
    ):
        ClaimEvidenceLinkingResult.validate(
            _usable_mapping(linking_executed=1)
        )


def test_empty_result_may_explicitly_record_not_executed():
    result = ClaimEvidenceLinkingResult(
        status="empty",
        claim_count=1,
        linked_claim_count=0,
        source_count=1,
        linking_executed=False,
    )

    assert result.status == "empty"
    assert result.links == ()
    assert result.linking_executed is False
    assert result.linked_claim_count == 0


def test_unavailable_result_may_explicitly_record_not_executed():
    result = ClaimEvidenceLinkingResult(
        status="unavailable",
        claim_count=1,
        linked_claim_count=0,
        source_count=1,
        linking_executed=False,
        reason="linking_not_executed",
    )

    assert result.status == "unavailable"
    assert result.linking_executed is False
    assert result.reason == "linking_not_executed"


def test_existing_empty_helper_remains_executed_true():
    result = ClaimEvidenceLinkingResult.empty_result(
        claim_count=1,
        source_count=1,
    )

    assert result.status == "empty"
    assert result.linking_executed is True


def test_existing_unavailable_helper_remains_executed_true():
    result = ClaimEvidenceLinkingResult.unavailable_result(
        "claim_extraction_unavailable",
        claim_count=1,
        source_count=1,
    )

    assert result.status == "unavailable"
    assert result.linking_executed is True


def test_production_linker_usable_result_records_execution_true():
    claims = ClaimExtractionResult.usable_result(
        (
            EvidenceClaim(
                text=CLAIM,
                source_refs=(SOURCE,),
            ),
        ),
        source_count=1,
    )

    result = ClaimEvidenceLinker().link_result(
        claims,
        {
            "status": "usable",
            "sources": [{"uri": SOURCE}],
        },
    )

    assert result.status == "usable"
    assert result.linking_executed is True
    assert result.linked_claim_count == 1


def test_production_linker_empty_result_records_execution_true():
    claims = ClaimExtractionResult.usable_result(
        (
            EvidenceClaim(
                text=CLAIM,
                source_refs=(SOURCE,),
            ),
        ),
        source_count=1,
    )

    result = ClaimEvidenceLinker().link_result(
        claims,
        {
            "status": "usable",
            "sources": [{"uri": "https://different.example"}],
        },
    )

    assert result.status == "empty"
    assert result.linking_executed is True
    assert result.linked_claim_count == 0


def test_valid_executed_linking_remains_compatible_with_supported_confidence():
    linking = ClaimEvidenceLinkingResult.usable_result(
        (_link(),),
        claim_count=1,
        source_count=1,
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

    assert linking["linking_executed"] is True
    assert confidence.claim_coverage == 1.0
    assert confidence.status == "supported"


def test_canonical_result_blocks_nonexecuted_full_coverage_before_confidence():
    with pytest.raises(
        ValueError,
        match="usable claim-evidence linking requires linking_executed to be True",
    ):
        ClaimEvidenceLinkingResult(
            status="usable",
            links=(_link(),),
            claim_count=1,
            linked_claim_count=1,
            source_count=1,
            linking_executed=False,
        )


def test_step197_linked_claim_count_integrity_remains_intact():
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
            linking_executed=True,
        )
