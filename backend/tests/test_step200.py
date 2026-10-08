"""Step 200 — canonical evidence-quality validation execution-state integrity."""

import pytest

from backend.app.reality.claim_conflict import ClaimConflictResult
from backend.app.reality.claim_evidence_linking import (
    ClaimEvidenceLink,
    ClaimEvidenceLinkingResult,
)
from backend.app.reality.confidence_signal_aggregator import (
    RealityConfidenceSignalAggregator,
)
from backend.app.reality.evidence_quality import EvidenceQualityValidator
from backend.app.reality.evidence_quality_validation import (
    EvidenceQualityValidationResult,
)
from backend.app.reality.evidence_quality_validation_normalizer import (
    EvidenceQualityValidationResultNormalizer,
)
from backend.app.reality.source_freshness import (
    SourceFreshnessAssessment,
    SourceFreshnessResult,
)


SOURCE = "https://example.com"
CLAIM = "The service is operational."


def _usable_mapping(*, validation_executed: object) -> dict:
    return {
        "status": "usable",
        "usable": True,
        "source_count": 1,
        "has_content": True,
        "provenance_complete": True,
        "issues": [],
        "validation_executed": validation_executed,
    }


def _supported_linking() -> dict:
    return ClaimEvidenceLinkingResult.usable_result(
        (
            ClaimEvidenceLink(
                claim_text=CLAIM,
                source_ref=SOURCE,
            ),
        ),
        claim_count=1,
        source_count=1,
    ).to_dict()


def _freshness() -> dict:
    return SourceFreshnessResult.usable_result(
        (
            SourceFreshnessAssessment(
                source_id="source-1",
                status="fresh",
                observed_at="2026-01-01T12:00:00Z",
                age_seconds=0,
                max_age_seconds=3600,
            ),
        )
    ).to_dict()


def _no_conflicts() -> dict:
    return ClaimConflictResult.empty_result(claim_count=1).to_dict()


def test_usable_result_rejects_false_execution_flag():
    with pytest.raises(
        ValueError,
        match="usable evidence quality requires validation_executed to be True",
    ):
        EvidenceQualityValidationResult(
            status="usable",
            usable=True,
            source_count=1,
            has_content=True,
            provenance_complete=True,
            issues=[],
            validation_executed=False,
        )


def test_mapping_normalizer_rejects_usable_false_execution_flag():
    with pytest.raises(
        ValueError,
        match="usable evidence quality requires validation_executed to be True",
    ):
        EvidenceQualityValidationResultNormalizer.normalize(
            _usable_mapping(validation_executed=False)
        )


def test_usable_true_execution_flag_remains_valid():
    result = EvidenceQualityValidationResultNormalizer.normalize(
        _usable_mapping(validation_executed=True)
    )

    assert result.status == "usable"
    assert result.usable is True
    assert result.validation_executed is True


def test_non_boolean_execution_flag_remains_rejected():
    with pytest.raises(
        ValueError,
        match="validation_executed must be a boolean",
    ):
        EvidenceQualityValidationResultNormalizer.normalize(
            _usable_mapping(validation_executed=1)
        )


def test_insufficient_result_may_explicitly_record_not_executed():
    result = EvidenceQualityValidationResult(
        status="insufficient",
        usable=False,
        source_count=1,
        has_content=False,
        provenance_complete=True,
        issues=["no_content"],
        validation_executed=False,
    )

    assert result.status == "insufficient"
    assert result.usable is False
    assert result.validation_executed is False


def test_not_required_result_may_explicitly_record_not_executed():
    result = EvidenceQualityValidationResult(
        status="not_required",
        usable=False,
        source_count=0,
        has_content=False,
        provenance_complete=True,
        issues=[],
        validation_executed=False,
    )

    assert result.status == "not_required"
    assert result.usable is False
    assert result.validation_executed is False


def test_existing_usable_helper_remains_executed_true():
    result = EvidenceQualityValidationResult.usable_result(
        source_count=1,
        has_content=True,
        provenance_complete=True,
    )

    assert result.status == "usable"
    assert result.usable is True
    assert result.validation_executed is True


def test_existing_insufficient_helper_remains_executed_true():
    result = EvidenceQualityValidationResult.insufficient_result(
        source_count=1,
        has_content=False,
        provenance_complete=True,
        issues=["no_content"],
    )

    assert result.status == "insufficient"
    assert result.validation_executed is True


def test_existing_not_required_helper_remains_executed_true():
    result = EvidenceQualityValidationResult.not_required_result(
        source_count=0,
        has_content=False,
        provenance_complete=True,
    )

    assert result.status == "not_required"
    assert result.validation_executed is True


def test_production_validator_usable_result_records_execution_true():
    result = EvidenceQualityValidator().validate_result(
        {
            "status": "completed",
            "sources": [
                {
                    "uri": SOURCE,
                    "title": "Example",
                }
            ],
            "content": CLAIM,
        }
    )

    assert result.status == "usable"
    assert result.usable is True
    assert result.validation_executed is True


def test_production_validator_insufficient_result_records_execution_true():
    result = EvidenceQualityValidator().validate_result(
        {
            "status": "completed",
            "sources": [{"uri": SOURCE}],
            "content": "",
        }
    )

    assert result.status == "insufficient"
    assert result.usable is False
    assert result.validation_executed is True


def test_production_validator_not_required_result_records_execution_true():
    result = EvidenceQualityValidator().validate_result(
        {
            "status": "not_required",
            "sources": [],
            "content": None,
        }
    )

    assert result.status == "not_required"
    assert result.usable is False
    assert result.validation_executed is True


def test_valid_executed_evidence_quality_remains_compatible_with_supported_confidence():
    quality = EvidenceQualityValidationResult.usable_result(
        source_count=1,
        has_content=True,
        provenance_complete=True,
    ).to_dict()

    confidence = RealityConfidenceSignalAggregator().aggregate_result(
        evidence_quality=quality,
        linking=_supported_linking(),
        freshness=_freshness(),
        conflicts=_no_conflicts(),
    )

    assert quality["validation_executed"] is True
    assert confidence.status == "supported"
    assert confidence.evidence_usable is True


def test_nonexecuted_insufficient_quality_cannot_be_supported():
    quality = EvidenceQualityValidationResult(
        status="insufficient",
        usable=False,
        source_count=1,
        has_content=False,
        provenance_complete=True,
        issues=["no_content"],
        validation_executed=False,
    ).to_dict()

    confidence = RealityConfidenceSignalAggregator().aggregate_result(
        evidence_quality=quality,
        linking=_supported_linking(),
        freshness=_freshness(),
        conflicts=_no_conflicts(),
    )

    assert confidence.status == "insufficient"
    assert confidence.evidence_usable is False
    assert "evidence_quality_insufficient" in confidence.signals


def test_nonexecuted_not_required_quality_cannot_be_supported():
    quality = EvidenceQualityValidationResult(
        status="not_required",
        usable=False,
        source_count=0,
        has_content=False,
        provenance_complete=True,
        issues=[],
        validation_executed=False,
    ).to_dict()

    confidence = RealityConfidenceSignalAggregator().aggregate_result(
        evidence_quality=quality,
        linking=_supported_linking(),
        freshness=_freshness(),
        conflicts=_no_conflicts(),
    )

    assert confidence.status == "insufficient"
    assert confidence.evidence_usable is False
    assert "external_evidence_not_required" in confidence.signals


def test_existing_usable_status_still_requires_usable_true():
    with pytest.raises(
        ValueError,
        match="usable status requires usable=True",
    ):
        EvidenceQualityValidationResult(
            status="usable",
            usable=False,
            source_count=1,
            has_content=True,
            provenance_complete=True,
            issues=[],
            validation_executed=True,
        )


def test_usable_result_rejects_zero_sources():
    with pytest.raises(
        ValueError,
        match="usable evidence quality requires at least one source",
    ):
        EvidenceQualityValidationResult(
            status="usable",
            usable=True,
            source_count=0,
            has_content=True,
            provenance_complete=True,
            issues=[],
            validation_executed=True,
        )


def test_usable_result_rejects_missing_content():
    with pytest.raises(
        ValueError,
        match="usable evidence quality requires has_content=True",
    ):
        EvidenceQualityValidationResult(
            status="usable",
            usable=True,
            source_count=1,
            has_content=False,
            provenance_complete=True,
            issues=[],
            validation_executed=True,
        )


def test_usable_result_rejects_incomplete_provenance():
    with pytest.raises(
        ValueError,
        match="usable evidence quality requires provenance_complete=True",
    ):
        EvidenceQualityValidationResult(
            status="usable",
            usable=True,
            source_count=1,
            has_content=True,
            provenance_complete=False,
            issues=[],
            validation_executed=True,
        )


def test_usable_result_rejects_validation_issues():
    with pytest.raises(
        ValueError,
        match="usable evidence quality cannot contain validation issues",
    ):
        EvidenceQualityValidationResult(
            status="usable",
            usable=True,
            source_count=1,
            has_content=True,
            provenance_complete=True,
            issues=["unexpected_issue"],
            validation_executed=True,
        )


def test_usable_helper_inherits_complete_usable_state_integrity():
    with pytest.raises(
        ValueError,
        match="usable evidence quality requires has_content=True",
    ):
        EvidenceQualityValidationResult.usable_result(
            source_count=1,
            has_content=False,
            provenance_complete=True,
        )
