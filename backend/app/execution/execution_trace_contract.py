from dataclasses import dataclass
from datetime import datetime
from typing import Any


@dataclass(frozen=True)
class ExecutionTraceEvent:
    """Canonical provider-neutral event emitted by the execution trace."""

    stage: str
    status: str
    timestamp: str
    metadata: dict[str, Any]

    def __post_init__(self) -> None:
        if not isinstance(self.stage, str) or not self.stage.strip():
            raise ValueError("stage must be a non-empty string")
        if not isinstance(self.status, str) or not self.status.strip():
            raise ValueError("status must be a non-empty string")
        if not isinstance(self.timestamp, str) or not self.timestamp.strip():
            raise ValueError("timestamp must be a non-empty string")
        try:
            parsed = datetime.fromisoformat(self.timestamp.replace("Z", "+00:00"))
        except ValueError as exc:
            raise ValueError("timestamp must be a valid ISO-8601 timestamp") from exc
        if parsed.tzinfo is None:
            raise ValueError("timestamp must include timezone information")
        if not isinstance(self.metadata, dict):
            raise ValueError("metadata must be a mapping")

    @classmethod
    def validate(cls, raw_event: object) -> "ExecutionTraceEvent":
        if isinstance(raw_event, cls):
            return raw_event
        if not isinstance(raw_event, dict):
            raise ValueError("execution trace event must be a mapping or ExecutionTraceEvent")
        required = {"stage", "status", "timestamp", "metadata"}
        missing = sorted(required - set(raw_event))
        if missing:
            raise ValueError(f"missing required fields: {', '.join(missing)}")
        metadata = raw_event["metadata"]
        if not isinstance(metadata, dict):
            raise ValueError("metadata must be a mapping")
        return cls(
            stage=raw_event["stage"],
            status=raw_event["status"],
            timestamp=raw_event["timestamp"],
            metadata=dict(metadata),
        )

    def to_dict(self) -> dict[str, Any]:
        return {
            "stage": self.stage,
            "status": self.status,
            "timestamp": self.timestamp,
            **dict(self.metadata),
        }


__all__ = ["ExecutionTraceEvent"]
