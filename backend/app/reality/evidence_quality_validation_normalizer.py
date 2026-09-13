from collections.abc import Mapping
from typing import Any

from backend.app.reality.evidence_quality_validation import EvidenceQualityValidationResult


class EvidenceQualityValidationResultNormalizer:
    """Normalize typed or legacy evidence-quality validation results."""

    @staticmethod
    def normalize(raw_result: object) -> EvidenceQualityValidationResult:
        if isinstance(raw_result, EvidenceQualityValidationResult):
            return raw_result

        if isinstance(raw_result, Mapping):
            values: dict[str, Any] = dict(raw_result)
            issues = values.get("issues", [])
            if not isinstance(issues, list):
                raise ValueError("evidence quality validation issues must be a list")
            return EvidenceQualityValidationResult(
                status=values["status"],
                usable=values["usable"],
                source_count=values["source_count"],
                has_content=values["has_content"],
                provenance_complete=values["provenance_complete"],
                issues=list(issues),
                validation_executed=values.get("validation_executed", True),
            )

        raise ValueError(
            "evidence quality validation result must be a result contract or mapping"
        )


__all__ = ["EvidenceQualityValidationResultNormalizer"]
