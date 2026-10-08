from typing import Any

from backend.app.reality.evidence_normalization import EvidenceNormalizationResult
from backend.app.reality.evidence_normalization_consumption_result import (
    EvidenceNormalizationConsumptionResult,
)


class EvidenceNormalizationConsumer:
    """Classify normalized evidence and return a stable consumption result."""

    def consume(self, evidence: object) -> EvidenceNormalizationConsumptionResult:
        evidence = EvidenceNormalizationResult.validate(evidence)

        status = evidence.status
        sources = evidence.sources
        content = evidence.content

        if status == "not_required":
            return EvidenceNormalizationConsumptionResult.usable_result(status)

        if status == "completed":
            if not isinstance(sources, list):
                return EvidenceNormalizationConsumptionResult.rejected_result(
                    status, "invalid_normalized_evidence_sources"
                )
            if content is not None and not isinstance(content, str):
                return EvidenceNormalizationConsumptionResult.rejected_result(
                    status, "invalid_normalized_evidence_content"
                )
            if not sources and not content:
                return EvidenceNormalizationConsumptionResult.rejected_result(
                    status, "empty_normalized_evidence"
                )
            return EvidenceNormalizationConsumptionResult.usable_result(status)

        if status == "invalid_evidence":
            return EvidenceNormalizationConsumptionResult.rejected_result(
                status, "invalid_evidence"
            )

        if status == "unknown":
            return EvidenceNormalizationConsumptionResult.rejected_result(
                status, "unknown_evidence_status"
            )

        return EvidenceNormalizationConsumptionResult.rejected_result(
            "unknown", "unsupported_evidence_status"
        )


__all__ = ["EvidenceNormalizationConsumer"]
