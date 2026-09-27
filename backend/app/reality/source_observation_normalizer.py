from collections.abc import Mapping

from backend.app.reality.source_observation import SourceObservationResult


class SourceObservationResultNormalizer:
    """Normalize typed or mapping-shaped source-observation results."""

    @staticmethod
    def normalize(raw_result: object) -> SourceObservationResult:
        if isinstance(raw_result, SourceObservationResult):
            return raw_result
        if isinstance(raw_result, Mapping):
            return SourceObservationResult.validate(dict(raw_result))
        raise ValueError(
            "source observation result must be a source-observation contract or mapping"
        )


__all__ = ["SourceObservationResultNormalizer"]
