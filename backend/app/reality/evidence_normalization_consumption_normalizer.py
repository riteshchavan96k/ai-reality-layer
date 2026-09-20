from collections.abc import Mapping

from backend.app.reality.evidence_normalization_consumption import (
    EvidenceNormalizationConsumption,
)


class EvidenceNormalizationConsumptionNormalizer:
    """Normalize typed or legacy evidence-normalization consumption decisions."""

    @staticmethod
    def normalize(
        raw_consumption: object,
    ) -> EvidenceNormalizationConsumption:
        if isinstance(raw_consumption, EvidenceNormalizationConsumption):
            return raw_consumption

        if isinstance(raw_consumption, Mapping):
            return EvidenceNormalizationConsumption.validate(dict(raw_consumption))

        raise ValueError(
            "evidence normalization consumption must be a consumption contract or mapping"
        )


__all__ = ["EvidenceNormalizationConsumptionNormalizer"]
