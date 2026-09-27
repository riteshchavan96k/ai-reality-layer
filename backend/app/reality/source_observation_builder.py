from datetime import datetime, timezone
from typing import Any, Callable

from backend.app.reality.source_observation import SourceObservation, SourceObservationResult
from backend.app.reality.source_observation_normalizer import SourceObservationResultNormalizer
from backend.app.reality.source_provenance import SourceProvenanceResult


class SourceObservationBuilder:
    """Attach retrieval-observation timestamps to stable source identities."""

    def __init__(self, clock: Callable[[], datetime] | None = None) -> None:
        self._clock = clock or (lambda: datetime.now(timezone.utc))

    def build_result(
        self,
        provenance: SourceProvenanceResult | dict[str, Any],
    ) -> SourceObservationResult:
        if isinstance(provenance, dict):
            provenance = self._provenance_from_mapping(provenance)
        if not isinstance(provenance, SourceProvenanceResult):
            raise ValueError("provenance must be a SourceProvenanceResult")

        if provenance.status == "unavailable":
            return SourceObservationResultNormalizer.normalize(
                SourceObservationResult.unavailable_result(
                    provenance.reason or "source_provenance_unavailable"
                )
            )
        if provenance.status == "empty":
            return SourceObservationResultNormalizer.normalize(SourceObservationResult.empty_result())

        observed_at = self._clock()
        if not isinstance(observed_at, datetime):
            raise ValueError("clock must return a datetime")
        if observed_at.tzinfo is None:
            raise ValueError("clock must return a timezone-aware datetime")
        observed_at_utc = observed_at.astimezone(timezone.utc)
        timestamp = observed_at_utc.isoformat().replace("+00:00", "Z")

        return SourceObservationResultNormalizer.normalize(
            SourceObservationResult.usable_result(
                tuple(
                    SourceObservation(source.source_id, timestamp)
                    for source in provenance.sources
                )
            )
        )

    def build(self, provenance: SourceProvenanceResult | dict[str, Any]) -> dict[str, Any]:
        return self.build_result(provenance).to_dict()

    @staticmethod
    def _provenance_from_mapping(value: dict[str, Any]) -> SourceProvenanceResult:
        if not isinstance(value, dict):
            raise ValueError("provenance must be a dictionary")
        raw_sources = value.get("sources", [])
        if not isinstance(raw_sources, list):
            raise ValueError("provenance sources must be a list")
        from backend.app.reality.source_provenance import SourceProvenance

        sources = tuple(
            SourceProvenance(
                source_id=item.get("source_id", ""),
                source_ref=item.get("source_ref", ""),
                uri=item.get("uri", ""),
                title=item.get("title"),
                identity_method=item.get("identity_method", "sha256_uri"),
            )
            for item in raw_sources
        )
        return SourceProvenanceResult(
            status=value.get("status"),
            sources=sources,
            source_count=value.get("source_count", len(sources)),
            provenance_executed=value.get("provenance_executed", True),
            reason=value.get("reason"),
        )


__all__ = ["SourceObservationBuilder"]
