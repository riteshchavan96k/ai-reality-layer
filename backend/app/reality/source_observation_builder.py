from datetime import datetime, timezone
from typing import Any, Callable

from backend.app.reality.source_observation import (
    SourceObservation,
    SourceObservationResult,
    normalize_reported_observation_time,
)
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

    def build_retrieval_result(
        self,
        provenance: SourceProvenanceResult | dict[str, Any],
        sources: list[dict[str, Any]],
        *,
        require_provider_observations: bool = False,
    ) -> SourceObservationResult:
        """Preserve reported per-source observation times for retrieved evidence.

        If the caller requests a freshness window, a provider-reported time is
        required for every source. Retrieval/ingestion time cannot substitute.
        """
        if not isinstance(sources, list) or any(
            not isinstance(source, dict) for source in sources
        ):
            raise ValueError("retrieval sources must be a list of mappings")
        if not isinstance(require_provider_observations, bool):
            raise ValueError("require_provider_observations must be a boolean")
        if isinstance(provenance, dict):
            provenance = self._provenance_from_mapping(provenance)
        if not isinstance(provenance, SourceProvenanceResult):
            raise ValueError("provenance must be a SourceProvenanceResult")
        if provenance.status != "usable":
            return self.build_result(provenance)

        by_uri = {source.get("uri"): source for source in sources}
        if (
            len(by_uri) != len(sources)
            or set(by_uri) != {source.uri for source in provenance.sources}
        ):
            return SourceObservationResult.unavailable_result(
                "retrieval_source_provenance_mismatch"
            )

        if require_provider_observations and any(
            "observed_at" not in source for source in sources
        ):
            return SourceObservationResult.unavailable_result(
                "provider_observation_required"
            )

        # Only the legacy fallback records current retrieval time. That time
        # is never used to satisfy an explicitly requested freshness policy.
        need_fallback = any(
            "observed_at" not in source for source in sources
        )
        fallback_timestamp = None
        if need_fallback:
            now = self._clock()
            if not isinstance(now, datetime) or now.tzinfo is None:
                raise ValueError("clock must return a timezone-aware datetime")
            fallback_timestamp = (
                now.astimezone(timezone.utc)
                .isoformat().replace("+00:00", "Z")
            )

        observations = []
        for source in provenance.sources:
            raw = by_uri[source.uri]
            if "observed_at" in raw:
                try:
                    timestamp = normalize_reported_observation_time(
                        raw["observed_at"]
                    )
                except ValueError:
                    return SourceObservationResult.unavailable_result(
                        "invalid_provider_observation_time"
                    )
                method = "retrieval_provider_observation"
            else:
                timestamp = fallback_timestamp
                method = "retrieval_observation"
            observations.append(SourceObservation(
                source.source_id,
                timestamp,
                observation_method=method,
            ))
        return SourceObservationResultNormalizer.normalize(
            SourceObservationResult.usable_result(tuple(observations))
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
