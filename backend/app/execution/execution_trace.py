from datetime import datetime, timezone
from typing import Any


class ExecutionTrace:
    """Lightweight in-memory trace of an orchestration lifecycle."""

    def __init__(self) -> None:
        self._events: list[dict[str, Any]] = []

    def record(self, stage: str, status: str, **metadata: Any) -> None:
        self._events.append(
            {
                "stage": stage,
                "status": status,
                "timestamp": datetime.now(timezone.utc).isoformat(),
                **metadata,
            }
        )

    def snapshot(self) -> list[dict[str, Any]]:
        return [dict(event) for event in self._events]
