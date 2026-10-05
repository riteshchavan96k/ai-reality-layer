from datetime import datetime, timezone
from typing import Any, Callable

from backend.app.reality.source_freshness import SourceFreshnessAssessment, SourceFreshnessResult
from backend.app.reality.source_freshness_normalizer import SourceFreshnessResultNormalizer
from backend.app.reality.source_observation import SourceObservationResult
from backend.app.reality.freshness_policy import is_positive_finite_number


class SourceFreshnessEvaluator:
    """Evaluate observation age only when an explicit freshness window is supplied."""

    def __init__(self, clock: Callable[[], datetime] | None = None) -> None:
        self._clock = clock or (lambda: datetime.now(timezone.utc))

    def evaluate_result(
        self,
        observations: SourceObservationResult | dict[str, Any],
        max_age_seconds: float | int | None = None,
    ) -> SourceFreshnessResult:
        if isinstance(observations, dict):
            observations = self._observations_from_mapping(observations)
        if not isinstance(observations, SourceObservationResult):
            raise ValueError("observations must be a SourceObservationResult")
        if max_age_seconds is not None:
            if not is_positive_finite_number(max_age_seconds):
                raise ValueError("max_age_seconds must be a positive number or None")

        if observations.status == "unavailable":
            return SourceFreshnessResultNormalizer.normalize(
                SourceFreshnessResult.unavailable_result(observations.reason or "source_observation_unavailable")
            )
        if observations.status == "empty":
            return SourceFreshnessResultNormalizer.normalize(SourceFreshnessResult.empty_result())

        now = self._clock()
        if not isinstance(now, datetime) or now.tzinfo is None:
            raise ValueError("clock must return a timezone-aware datetime")
        now_utc = now.astimezone(timezone.utc)
        assessments = []
        for observation in observations.observations:
            observed_at = datetime.fromisoformat(observation.observed_at.replace("Z", "+00:00"))
            observed_utc = observed_at.astimezone(timezone.utc)
            age_seconds = (now_utc - observed_utc).total_seconds()
            if age_seconds < 0:
                raise ValueError("observation timestamp cannot be in the future")
            if max_age_seconds is None:
                assessments.append(SourceFreshnessAssessment(
                    source_id=observation.source_id,
                    status="unknown",
                    observed_at=observation.observed_at,
                    reason="freshness_window_not_declared",
                ))
            else:
                status = "fresh" if age_seconds <= max_age_seconds else "stale"
                assessments.append(SourceFreshnessAssessment(
                    source_id=observation.source_id,
                    status=status,
                    observed_at=observation.observed_at,
                    age_seconds=age_seconds,
                    max_age_seconds=float(max_age_seconds),
                ))
        return SourceFreshnessResultNormalizer.normalize(
            SourceFreshnessResult.usable_result(tuple(assessments))
        )

    def evaluate(self, observations: SourceObservationResult | dict[str, Any], max_age_seconds: float | int | None = None) -> dict[str, Any]:
        return self.evaluate_result(observations, max_age_seconds=max_age_seconds).to_dict()

    @staticmethod
    def _observations_from_mapping(value: dict[str, Any]) -> SourceObservationResult:
        if not isinstance(value, dict):
            raise ValueError("observations must be a dictionary")
        from backend.app.reality.source_observation import SourceObservation

        raw = value.get("observations", [])
        if not isinstance(raw, list):
            raise ValueError("observations must be a list")
        items = tuple(SourceObservation(item.get("source_id", ""), item.get("observed_at", ""), item.get("observation_method", "retrieval_observation")) for item in raw)
        return SourceObservationResult(
            status=value.get("status"),
            observations=items,
            source_count=value.get("source_count", len(items)),
            observation_executed=value.get("observation_executed", True),
            reason=value.get("reason"),
        )


__all__ = ["SourceFreshnessEvaluator"]
