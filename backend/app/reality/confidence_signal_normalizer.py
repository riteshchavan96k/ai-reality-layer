from collections.abc import Mapping

from backend.app.reality.confidence_signals import RealityConfidenceSignalResult


class RealityConfidenceSignalResultNormalizer:
    """Normalize typed or mapping-shaped confidence-signal results."""

    @staticmethod
    def normalize(raw_result: object) -> RealityConfidenceSignalResult:
        if isinstance(raw_result, RealityConfidenceSignalResult):
            return raw_result
        if isinstance(raw_result, Mapping):
            return RealityConfidenceSignalResult.validate(dict(raw_result))
        raise ValueError(
            "confidence signal result must be a confidence-signal contract or mapping"
        )


__all__ = ["RealityConfidenceSignalResultNormalizer"]
