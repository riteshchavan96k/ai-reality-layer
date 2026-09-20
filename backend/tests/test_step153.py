import pytest

from backend.app.reality.evidence_normalization_consumption import (
    EvidenceNormalizationConsumption,
)
from backend.app.reality.evidence_normalization_consumption_normalizer import (
    EvidenceNormalizationConsumptionNormalizer,
)


def test_step153_accepts_canonical_consumption_contract():
    result = EvidenceNormalizationConsumption.usable_result("completed")

    assert EvidenceNormalizationConsumption.validate(result) is result


def test_step153_normalizes_compatible_mapping():
    result = EvidenceNormalizationConsumptionNormalizer.normalize(
        {
            "status": "usable",
            "evidence_status": "completed",
            "usable": True,
            "reason": None,
            "consumption_executed": True,
        }
    )

    assert result.status == "usable"
    assert result.evidence_status == "completed"
    assert result.usable is True


def test_step153_rejects_missing_required_field():
    with pytest.raises(ValueError, match="missing required fields"):
        EvidenceNormalizationConsumption.validate(
            {
                "status": "usable",
                "evidence_status": "completed",
                "usable": True,
            }
        )


def test_step153_rejects_status_usability_inconsistency():
    with pytest.raises(ValueError, match="usable status requires usable=True"):
        EvidenceNormalizationConsumption.validate(
            {
                "status": "usable",
                "evidence_status": "completed",
                "usable": False,
                "reason": None,
                "consumption_executed": True,
            }
        )


def test_step153_rejects_invalid_evidence_status():
    with pytest.raises(ValueError, match="evidence_status must be a supported evidence status"):
        EvidenceNormalizationConsumptionNormalizer.normalize(
            {
                "status": "usable",
                "evidence_status": "unsupported",
                "usable": True,
                "reason": None,
                "consumption_executed": True,
            }
        )
