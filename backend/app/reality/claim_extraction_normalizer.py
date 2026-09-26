from collections.abc import Mapping

from backend.app.reality.claim_extraction import ClaimExtractionResult


class ClaimExtractionResultNormalizer:
    """Normalize typed or legacy claim-extraction results."""

    @staticmethod
    def normalize(raw_result: object) -> ClaimExtractionResult:
        if isinstance(raw_result, ClaimExtractionResult):
            return raw_result

        if isinstance(raw_result, Mapping):
            return ClaimExtractionResult.validate(dict(raw_result))

        raise ValueError(
            "claim extraction result must be a claim-extraction contract or mapping"
        )


__all__ = ["ClaimExtractionResultNormalizer"]
