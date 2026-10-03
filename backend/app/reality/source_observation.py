from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Any


@dataclass(frozen=True)
class SourceObservation:
    """Record when a source was observed, with explicit observation provenance."""

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
        if self.observation_method not in {
            "retrieval_observation",
            "submitted_evidence_observation",
            "submitted_evidence_ingestion",
        }:
            raise ValueError(
                "observation_method must be retrieval_observation, "
                "submitted_evidence_observation, or submitted_evidence_ingestion"
            )

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
        if not isinstance(self.source_count, int) or self.source_count < 0:
            raise ValueError("source_count must be a non-negative integer")
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

    @classmethod
    def validate(cls, raw_result: object) -> "SourceObservationResult":
        """Validate or normalize a canonical source-observation result."""
        if isinstance(raw_result, cls):
            return raw_result
        if not isinstance(raw_result, dict):
            raise ValueError("source observation result must be a mapping or SourceObservationResult")
        required = {"status", "observations", "source_count", "observation_executed", "reason"}
        missing = sorted(required - set(raw_result))
        if missing:
            raise ValueError(f"missing required fields: {', '.join(missing)}")
        raw_observations = raw_result["observations"]
        if not isinstance(raw_observations, (list, tuple)):
            raise ValueError("observations must be a list or tuple")
        observations: list[SourceObservation] = []
        for raw_observation in raw_observations:
            if isinstance(raw_observation, SourceObservation):
                observations.append(raw_observation)
                continue
            if not isinstance(raw_observation, dict):
                raise ValueError("each source observation must be a mapping or SourceObservation")
            observation_required = {"source_id", "observed_at", "observation_method"}
            observation_missing = sorted(observation_required - set(raw_observation))
            if observation_missing:
                raise ValueError(f"source observation is missing required fields: {', '.join(observation_missing)}")
            observations.append(
                SourceObservation(
                    source_id=raw_observation["source_id"],
                    observed_at=raw_observation["observed_at"],
                    observation_method=raw_observation["observation_method"],
                )
            )
        return cls(
            status=raw_result["status"],
            observations=tuple(observations),
            source_count=raw_result["source_count"],
            observation_executed=raw_result["observation_executed"],
            reason=raw_result["reason"],
        )

    def to_dict(self) -> dict[str, Any]:
        return {
            "status": self.status,
            "observations": [item.to_dict() for item in self.observations],
            "source_count": self.source_count,
            "observation_executed": self.observation_executed,
            "reason": self.reason,
        }


__all__ = ["SourceObservation", "SourceObservationResult"]
