from typing import Any

from backend.app.reality.evidence_normalization_consumption import EvidenceNormalizationConsumption


class EvidenceNormalizationConsumer:
    """Classify normalized evidence before evidence-quality validation."""

    def consume(self, evidence: object) -> EvidenceNormalizationConsumption:
        if not isinstance(evidence, dict):
            raise ValueError("normalized evidence must be a dictionary")

        status = evidence.get("status")
        sources = evidence.get("sources", [])
        content = evidence.get("content")

        if status == "not_required":
            return EvidenceNormalizationConsumption.usable_result(status)

        if status == "completed":
            if not isinstance(sources, list):
                return EvidenceNormalizationConsumption.rejected_result(
                    status, "invalid_normalized_evidence_sources"
                )
            if content is not None and not isinstance(content, str):
                return EvidenceNormalizationConsumption.rejected_result(
                    status, "invalid_normalized_evidence_content"
                )
            if not sources and not content:
                return EvidenceNormalizationConsumption.rejected_result(
                    status, "empty_normalized_evidence"
                )
            return EvidenceNormalizationConsumption.usable_result(status)

        if status == "invalid_evidence":
            return EvidenceNormalizationConsumption.rejected_result(
                status, "invalid_evidence"
            )

        if status == "unknown":
            return EvidenceNormalizationConsumption.rejected_result(
                status, "unknown_evidence_status"
            )

        return EvidenceNormalizationConsumption.rejected_result(
            str(status), "unsupported_evidence_status"
        )


__all__ = ["EvidenceNormalizationConsumer"]
