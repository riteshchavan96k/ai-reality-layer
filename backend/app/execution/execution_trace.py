from datetime import datetime, timezone
from typing import Any

from backend.app.execution.execution_trace_contract import ExecutionTraceEvent
from backend.app.execution.execution_trace_normalizer import ExecutionTraceEventNormalizer


class ExecutionTrace:
    """Lightweight in-memory trace of an orchestration lifecycle."""

    def __init__(self) -> None:
        self._events: list[ExecutionTraceEvent] = []

    def record(self, stage: str, status: str, **metadata: Any) -> None:
        event = ExecutionTraceEventNormalizer.normalize(
            {
                "stage": stage,
                "status": status,
                "timestamp": datetime.now(timezone.utc).isoformat(),
                "metadata": metadata,
            }
        )
        self._events.append(event)

    def snapshot(self) -> list[dict[str, Any]]:
        return [event.to_dict() for event in self._events]
