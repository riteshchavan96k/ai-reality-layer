from typing import Any

from backend.app.execution.execution_trace_snapshot_contract import ExecutionTraceSnapshot


class ExecutionTraceSnapshotNormalizer:
    """Canonical normalization boundary for execution-trace snapshots."""

    @staticmethod
    def normalize(raw_snapshot: object) -> ExecutionTraceSnapshot:
        if isinstance(raw_snapshot, ExecutionTraceSnapshot):
            return raw_snapshot
        if isinstance(raw_snapshot, list) and all(isinstance(item, dict) for item in raw_snapshot):
            events: list[dict[str, Any]] = []
            for item in raw_snapshot:
                metadata = {
                    key: value
                    for key, value in item.items()
                    if key not in {"stage", "status", "timestamp"}
                }
                events.append(
                    {
                        "stage": item.get("stage"),
                        "status": item.get("status"),
                        "timestamp": item.get("timestamp"),
                        "metadata": metadata,
                    }
                )
            return ExecutionTraceSnapshot.validate(events)
        return ExecutionTraceSnapshot.validate(raw_snapshot)


__all__ = ["ExecutionTraceSnapshotNormalizer"]
