from collections.abc import Mapping

from backend.app.reality.evidence_normalization_consumption import (
    EvidenceNormalizationConsumption,
)
from backend.app.reality.evidence_normalization_consumption_result import (
    EvidenceNormalizationConsumptionResult,
)


class EvidenceNormalizationConsumptionNormalizer:
    """Normalize typed or legacy evidence-normalization consumption decisions."""

    @staticmethod
    def normalize(
        raw_consumption: object,
    ) -> EvidenceNormalizationConsumption:
        if isinstance(raw_consumption, EvidenceNormalizationConsumption):
            return raw_consumption

        if isinstance(raw_consumption, EvidenceNormalizationConsumptionResult):
            return EvidenceNormalizationConsumption(
                status=raw_consumption.status,
                evidence_status=raw_consumption.evidence_status,
                usable=raw_consumption.usable,
                reason=raw_consumption.reason,
                consumption_executed=raw_consumption.consumption_evaluated,
            )

        if isinstance(raw_consumption, Mapping):
            return EvidenceNormalizationConsumption.validate(dict(raw_consumption))

        raise ValueError(
            "evidence normalization consumption must be a consumption contract or mapping"
        )


__all__ = ["EvidenceNormalizationConsumptionNormalizer"]
