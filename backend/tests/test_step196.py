"""Step 196 — canonical claim-conflict execution-state integrity."""

import pytest

from backend.app.reality.claim_conflict import ClaimConflict, ClaimConflictResult
from backend.app.reality.claim_conflict_detector import ClaimConflictDetector
from backend.app.reality.claim_conflict_normalizer import (
    ClaimConflictResultNormalizer,
)
from backend.app.reality.claim_extraction import ClaimExtractionResult, EvidenceClaim
from backend.app.reality.confidence_signal_aggregator import (
    RealityConfidenceSignalAggregator,
)


def _conflict() -> ClaimConflict:
    return ClaimConflict(
        claim_a="available",
        claim_b="not available",
        source_refs_a=("https://a.example",),
        source_refs_b=("https://b.example",),
    )


def _usable_mapping(*, detection_executed: object) -> dict:
    return {
        "status": "usable",
        "conflicts": [_conflict().to_dict()],
        "conflict_count": 1,
        "claim_count": 2,
        "detection_executed": detection_executed,
        "reason": None,
    }


def _empty_mapping(*, detection_executed: object) -> dict:
    return {
        "status": "empty",
        "conflicts": [],
        "conflict_count": 0,
        "claim_count": 2,
        "detection_executed": detection_executed,
        "reason": None,
    }


def test_usable_result_rejects_false_execution_flag():
    with pytest.raises(
        ValueError,
        match="usable or empty conflict result requires detection_executed to be True",
    ):
        ClaimConflictResult(
            status="usable",
            conflicts=(_conflict(),),
            claim_count=2,
            conflict_count=1,
            detection_executed=False,
        )


def test_empty_result_rejects_false_execution_flag():
    with pytest.raises(
        ValueError,
        match="usable or empty conflict result requires detection_executed to be True",
    ):
        ClaimConflictResult(
            status="empty",
            claim_count=2,
            conflict_count=0,
            detection_executed=False,
        )


def test_mapping_rejects_usable_false_execution_flag():
    with pytest.raises(
        ValueError,
        match="usable or empty conflict result requires detection_executed to be True",
    ):
        ClaimConflictResult.validate(
            _usable_mapping(detection_executed=False)
        )


def test_mapping_rejects_empty_false_execution_flag():
    with pytest.raises(
        ValueError,
        match="usable or empty conflict result requires detection_executed to be True",
    ):
        ClaimConflictResult.validate(
            _empty_mapping(detection_executed=False)
        )


def test_normalizer_rejects_empty_false_execution_flag():
    with pytest.raises(
        ValueError,
        match="usable or empty conflict result requires detection_executed to be True",
    ):
        ClaimConflictResultNormalizer.normalize(
            _empty_mapping(detection_executed=False)
        )


def test_usable_true_execution_flag_remains_valid():
    result = ClaimConflictResult.validate(
        _usable_mapping(detection_executed=True)
    )

    assert result.status == "usable"
    assert result.detection_executed is True
    assert result.conflict_count == 1


def test_empty_true_execution_flag_remains_valid():
    result = ClaimConflictResult.validate(
        _empty_mapping(detection_executed=True)
    )

    assert result.status == "empty"
    assert result.detection_executed is True
    assert result.conflict_count == 0


def test_non_boolean_execution_flag_remains_rejected():
    with pytest.raises(
        ValueError,
        match="detection_executed must be a boolean",
    ):
        ClaimConflictResult.validate(
            _empty_mapping(detection_executed=1)
        )


def test_unavailable_result_may_explicitly_record_not_executed():
    result = ClaimConflictResult(
        status="unavailable",
        claim_count=2,
        conflict_count=0,
        detection_executed=False,
        reason="conflict_detection_not_executed",
    )

    assert result.status == "unavailable"
    assert result.detection_executed is False
    assert result.reason == "conflict_detection_not_executed"


def test_existing_unavailable_helper_remains_executed_true():
    result = ClaimConflictResult.unavailable_result(
        "claim_extraction_unavailable",
        claim_count=2,
    )

    assert result.status == "unavailable"
    assert result.detection_executed is True


def test_detector_conflict_result_records_execution_true():
    claims = ClaimExtractionResult.usable_result(
        (
            EvidenceClaim(
                "available",
                ("https://a.example",),
            ),
            EvidenceClaim(
                "not available",
                ("https://b.example",),
            ),
        ),
        source_count=2,
    )

    result = ClaimConflictDetector().detect_result(claims)

    assert result.status == "usable"
    assert result.detection_executed is True
    assert result.conflict_count == 1


def test_detector_zero_conflict_result_records_execution_true():
    claims = ClaimExtractionResult.usable_result(
        (
            EvidenceClaim(
                "available",
                ("https://a.example",),
            ),
            EvidenceClaim(
                "service operational",
                ("https://b.example",),
            ),
        ),
        source_count=2,
    )

    result = ClaimConflictDetector().detect_result(claims)

    assert result.status == "empty"
    assert result.detection_executed is True
    assert result.conflict_count == 0


def test_detector_unavailable_result_preserves_existing_execution_semantics():
    claims = ClaimExtractionResult.unavailable_result(
        "claim_extraction_unavailable",
        source_count=0,
    )

    result = ClaimConflictDetector().detect_result(claims)

    assert result.status == "unavailable"
    assert result.detection_executed is True


def test_executed_empty_conflict_result_remains_compatible_with_supported_confidence():
    conflicts = ClaimConflictResult.empty_result(claim_count=1).to_dict()

    result = RealityConfidenceSignalAggregator().aggregate_result(
        evidence_quality={"status": "usable"},
        linking={
            "status": "usable",
            "claim_count": 1,
            "linked_claim_count": 1,
        },
        freshness={
            "status": "usable",
            "stale_count": 0,
            "unknown_count": 0,
        },
        conflicts=conflicts,
    )

    assert conflicts["detection_executed"] is True
    assert result.status == "supported"
    assert result.conflict_count == 0


def test_unavailable_nonexecuted_conflict_result_cannot_be_positive_confidence():
    conflicts = ClaimConflictResult(
        status="unavailable",
        claim_count=1,
        conflict_count=0,
        detection_executed=False,
        reason="conflict_detection_not_executed",
    ).to_dict()

    result = RealityConfidenceSignalAggregator().aggregate_result(
        evidence_quality={"status": "usable"},
        linking={
            "status": "usable",
            "claim_count": 1,
            "linked_claim_count": 1,
        },
        freshness={
            "status": "usable",
            "stale_count": 0,
            "unknown_count": 0,
        },
        conflicts=conflicts,
    )

    assert result.status == "uncertain"
    assert "conflict_detection_unavailable" in result.signals


def test_conflict_count_consistency_remains_intact():
    with pytest.raises(
        ValueError,
        match="conflict_count must match conflicts",
    ):
        ClaimConflictResult(
            status="usable",
            conflicts=(_conflict(),),
            claim_count=2,
            conflict_count=0,
            detection_executed=True,
        )
