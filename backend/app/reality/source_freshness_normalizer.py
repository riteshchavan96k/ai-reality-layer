from collections.abc import Mapping

from backend.app.reality.source_freshness import SourceFreshnessResult


class SourceFreshnessResultNormalizer:
    """Normalize typed or mapping-shaped source-freshness results."""

    @staticmethod
    def normalize(raw_result: object) -> SourceFreshnessResult:
        if isinstance(raw_result, SourceFreshnessResult):
            return raw_result
        if isinstance(raw_result, Mapping):
            return SourceFreshnessResult.validate(dict(raw_result))
        raise ValueError(
            "source freshness result must be a freshness contract or mapping"
        )


__all__ = ["SourceFreshnessResultNormalizer"]
