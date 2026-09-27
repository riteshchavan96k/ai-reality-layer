from collections.abc import Mapping

from backend.app.reality.source_provenance import SourceProvenanceResult


class SourceProvenanceResultNormalizer:
    """Normalize typed or mapping-shaped source-provenance results."""

    @staticmethod
    def normalize(raw_result: object) -> SourceProvenanceResult:
        if isinstance(raw_result, SourceProvenanceResult):
            return raw_result
        if isinstance(raw_result, Mapping):
            return SourceProvenanceResult.validate(dict(raw_result))
        raise ValueError(
            "source provenance result must be a source-provenance contract or mapping"
        )


__all__ = ["SourceProvenanceResultNormalizer"]
