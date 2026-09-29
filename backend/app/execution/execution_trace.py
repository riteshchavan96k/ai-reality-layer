from datetime import datetime, timezone
from typing import Any

from backend.app.execution.execution_trace_contract import ExecutionTraceEvent
from backend.app.execution.execution_trace_normalizer import ExecutionTraceEventNormalizer
from backend.app.execution.execution_trace_snapshot_contract import ExecutionTraceSnapshot
from backend.app.execution.execution_trace_snapshot_normalizer import ExecutionTraceSnapshotNormalizer


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

    def snapshot_result(self) -> ExecutionTraceSnapshot:
        return ExecutionTraceSnapshot.from_events(self._events)

    def snapshot(self) -> list[dict[str, Any]]:
        snapshot = ExecutionTraceSnapshotNormalizer.normalize(self.snapshot_result())
        return snapshot.to_list()
