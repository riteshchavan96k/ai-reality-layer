"""Step 199 — canonical claim-extraction execution-state integrity."""

import pytest

from backend.app.reality.claim_conflict_detector import ClaimConflictDetector
from backend.app.reality.claim_evidence_linker import ClaimEvidenceLinker
from backend.app.reality.claim_extraction import ClaimExtractionResult, EvidenceClaim
from backend.app.reality.claim_extraction_normalizer import (
    ClaimExtractionResultNormalizer,
)
from backend.app.reality.claim_extractor import EvidenceClaimExtractor
from backend.app.reality.confidence_signal_aggregator import (
    RealityConfidenceSignalAggregator,
)


CLAIM = "The service is operational."
SOURCE = "https://example.com"


def _claim() -> EvidenceClaim:
    return EvidenceClaim(
        text=CLAIM,
        source_refs=(SOURCE,),
    )


def _usable_mapping(*, extraction_executed: object) -> dict:
    return {
        "status": "usable",
        "claims": [_claim().to_dict()],
        "source_count": 1,
        "extraction_executed": extraction_executed,
        "reason": None,
    }


def test_usable_result_rejects_false_execution_flag():
    with pytest.raises(
        ValueError,
        match="usable claim extraction requires extraction_executed to be True",
    ):
        ClaimExtractionResult(
            status="usable",
            claims=(_claim(),),
            source_count=1,
            extraction_executed=False,
        )


def test_mapping_rejects_usable_false_execution_flag():
    with pytest.raises(
        ValueError,
        match="usable claim extraction requires extraction_executed to be True",
    ):
        ClaimExtractionResult.validate(
            _usable_mapping(extraction_executed=False)
        )


def test_normalizer_rejects_usable_false_execution_flag():
    with pytest.raises(
        ValueError,
        match="usable claim extraction requires extraction_executed to be True",
    ):
        ClaimExtractionResultNormalizer.normalize(
            _usable_mapping(extraction_executed=False)
        )


def test_usable_true_execution_flag_remains_valid():
    result = ClaimExtractionResult.validate(
        _usable_mapping(extraction_executed=True)
    )

    assert result.status == "usable"
    assert result.extraction_executed is True
    assert len(result.claims) == 1


def test_non_boolean_execution_flag_remains_rejected():
    with pytest.raises(
        ValueError,
        match="extraction_executed must be a boolean",
    ):
        ClaimExtractionResult.validate(
            _usable_mapping(extraction_executed=1)
        )


def test_empty_result_may_explicitly_record_not_executed():
    result = ClaimExtractionResult(
        status="empty",
        source_count=1,
        extraction_executed=False,
    )

    assert result.status == "empty"
    assert result.claims == ()
    assert result.extraction_executed is False


def test_unavailable_result_may_explicitly_record_not_executed():
    result = ClaimExtractionResult(
        status="unavailable",
        source_count=1,
        extraction_executed=False,
        reason="extraction_not_executed",
    )

    assert result.status == "unavailable"
    assert result.claims == ()
    assert result.extraction_executed is False
    assert result.reason == "extraction_not_executed"


def test_existing_empty_helper_remains_executed_true():
    result = ClaimExtractionResult.empty_result(source_count=1)

    assert result.status == "empty"
    assert result.extraction_executed is True


def test_existing_unavailable_helper_remains_executed_true():
    result = ClaimExtractionResult.unavailable_result(
        "evidence_not_usable",
        source_count=1,
    )

    assert result.status == "unavailable"
    assert result.extraction_executed is True


def test_linker_rejects_mapping_that_denies_extraction_execution():
    with pytest.raises(
        ValueError,
        match="usable claim extraction requires extraction_executed to be True",
    ):
        ClaimEvidenceLinker().link_result(
            _usable_mapping(extraction_executed=False),
            {
                "status": "usable",
                "sources": [{"uri": SOURCE}],
            },
        )


def test_conflict_detector_rejects_mapping_that_denies_extraction_execution():
    with pytest.raises(
        ValueError,
        match="usable claim extraction requires extraction_executed to be True",
    ):
        ClaimConflictDetector().detect_result(
            _usable_mapping(extraction_executed=False)
        )


def test_production_extractor_usable_result_records_execution_true():
    result = EvidenceClaimExtractor().extract_result(
        {
            "status": "usable",
            "content": CLAIM,
            "sources": [{"uri": SOURCE}],
        }
    )

    assert result.status == "usable"
    assert result.extraction_executed is True
    assert len(result.claims) == 1


def test_production_extractor_empty_result_records_execution_true():
    result = EvidenceClaimExtractor().extract_result(
        {
            "status": "usable",
            "content": "",
            "sources": [{"uri": SOURCE}],
        }
    )

    assert result.status == "empty"
    assert result.extraction_executed is True


def test_production_extractor_unavailable_result_records_execution_true():
    result = EvidenceClaimExtractor().extract_result(
        {
            "status": "unavailable",
            "reason": "evidence_not_usable",
            "sources": [{"uri": SOURCE}],
        }
    )

    assert result.status == "unavailable"
    assert result.extraction_executed is True


def test_valid_extraction_flows_to_executed_linking_and_supported_confidence():
    extraction = ClaimExtractionResult.usable_result(
        (_claim(),),
        source_count=1,
    )
    linking = ClaimEvidenceLinker().link_result(
        extraction,
        {
            "status": "usable",
            "sources": [{"uri": SOURCE}],
        },
    )

    confidence = RealityConfidenceSignalAggregator().aggregate_result(
        evidence_quality={"status": "usable"},
        linking=linking.to_dict(),
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

    assert extraction.extraction_executed is True
    assert linking.status == "usable"
    assert linking.linking_executed is True
    assert linking.linked_claim_count == 1
    assert confidence.claim_coverage == 1.0
    assert confidence.status == "supported"


def test_step198_linking_execution_integrity_remains_intact():
    extraction = ClaimExtractionResult.usable_result(
        (_claim(),),
        source_count=1,
    )
    linking = ClaimEvidenceLinker().link_result(
        extraction,
        {
            "status": "usable",
            "sources": [{"uri": SOURCE}],
        },
    )

    assert linking.status == "usable"
    assert linking.linking_executed is True


def test_usable_result_still_requires_claims():
    with pytest.raises(
        ValueError,
        match="usable claim extraction requires at least one claim",
    ):
        ClaimExtractionResult(
            status="usable",
            claims=(),
            source_count=1,
            extraction_executed=True,
        )
