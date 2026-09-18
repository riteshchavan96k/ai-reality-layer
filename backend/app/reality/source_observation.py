from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Any


@dataclass(frozen=True)
class SourceObservation:
    """Record when a source was observed by the retrieval pipeline."""

    source_id: str
    observed_at: str
    observation_method: str = "retrieval_observation"

    def __post_init__(self) -> None:
        if not isinstance(self.source_id, str) or not self.source_id.strip():
            raise ValueError("source_id must be a non-empty string")
        if not isinstance(self.observed_at, str) or not self.observed_at.strip():
            raise ValueError("observed_at must be a non-empty string")
        try:
            parsed = datetime.fromisoformat(self.observed_at.replace("Z", "+00:00"))
        except ValueError as exc:
            raise ValueError("observed_at must be a valid ISO-8601 timestamp") from exc
        if parsed.tzinfo is None:
            raise ValueError("observed_at must include a timezone")
        if parsed.astimezone(timezone.utc) > datetime.now(timezone.utc):
            raise ValueError("observed_at cannot be in the future")
        if self.observation_method != "retrieval_observation":
            raise ValueError("observation_method must be retrieval_observation")

    def to_dict(self) -> dict[str, Any]:
        return {
            "source_id": self.source_id,
            "observed_at": self.observed_at,
            "observation_method": self.observation_method,
        }


@dataclass(frozen=True)
class SourceObservationResult:
    """Canonical result for source observation metadata."""

    status: str
    observations: tuple[SourceObservation, ...] = ()
    source_count: int = 0
    observation_executed: bool = True
    reason: str | None = None

    def __post_init__(self) -> None:
        if self.status not in {"usable", "empty", "unavailable"}:
            raise ValueError("status must be usable, empty, or unavailable")
        if not isinstance(self.observations, tuple) or any(not isinstance(item, SourceObservation) for item in self.observations):
            raise ValueError("observations must be a tuple of SourceObservation values")
        if self.source_count != len(self.observations):
            raise ValueError("source_count must match the number of observations")
        if not isinstance(self.observation_executed, bool):
            raise ValueError("observation_executed must be a boolean")
        if self.status == "usable" and not self.observations:
            raise ValueError("usable source observation requires observations")
        if self.status == "empty" and self.observations:
            raise ValueError("empty source observation cannot contain observations")
        if self.status == "unavailable" and self.observations:
            raise ValueError("unavailable source observation cannot contain observations")
        if self.status == "unavailable" and (not isinstance(self.reason, str) or not self.reason.strip()):
            raise ValueError("unavailable source observation requires a reason")
        if self.status != "unavailable" and self.reason is not None:
            raise ValueError("usable or empty source observation cannot contain a reason")

    @classmethod
    def usable_result(cls, observations: tuple[SourceObservation, ...]) -> "SourceObservationResult":
        return cls("usable", observations=observations, source_count=len(observations))

    @classmethod
    def empty_result(cls) -> "SourceObservationResult":
        return cls("empty")

    @classmethod
    def unavailable_result(cls, reason: str) -> "SourceObservationResult":
        return cls("unavailable", reason=reason)

    def to_dict(self) -> dict[str, Any]:
        return {
            "status": self.status,
            "observations": [item.to_dict() for item in self.observations],
            "source_count": self.source_count,
            "observation_executed": self.observation_executed,
            "reason": self.reason,
        }


__all__ = ["SourceObservation", "SourceObservationResult"]
