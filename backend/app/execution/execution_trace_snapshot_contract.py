from dataclasses import dataclass
from typing import Any, Iterable

from backend.app.execution.execution_trace_contract import ExecutionTraceEvent


@dataclass(frozen=True)
class ExecutionTraceSnapshot:
    """Canonical immutable snapshot of an execution trace."""

    events: tuple[ExecutionTraceEvent, ...]

    def __post_init__(self) -> None:
        if not isinstance(self.events, tuple):
            raise ValueError("events must be a tuple")
        for event in self.events:
            ExecutionTraceEvent.validate(event)

    @classmethod
    def validate(cls, raw_snapshot: object) -> "ExecutionTraceSnapshot":
        if isinstance(raw_snapshot, cls):
            return raw_snapshot
        if not isinstance(raw_snapshot, (list, tuple)):
            raise ValueError("execution trace snapshot must be a list, tuple, or ExecutionTraceSnapshot")
        events = tuple(ExecutionTraceEvent.validate(event) for event in raw_snapshot)
        return cls(events=events)

    @classmethod
    def from_events(cls, events: Iterable[ExecutionTraceEvent]) -> "ExecutionTraceSnapshot":
        return cls(events=tuple(ExecutionTraceEvent.validate(event) for event in events))

    @property
    def event_count(self) -> int:
        return len(self.events)

    def to_list(self) -> list[dict[str, Any]]:
        return [event.to_dict() for event in self.events]


__all__ = ["ExecutionTraceSnapshot"]
