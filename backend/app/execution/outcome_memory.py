from datetime import datetime, timezone
from hashlib import sha256
from typing import Any


class OutcomeMemory:
    """Bounded in-memory store of structured execution outcomes for future optimization."""

    def __init__(self, max_records: int = 1000) -> None:
        if max_records < 1:
            raise ValueError("max_records must be at least 1")

        self.max_records = max_records
        self._records: list[dict[str, Any]] = []
        self._next_id = 1

    def record(
        self,
        task: str,
        analysis: dict[str, Any],
        routing: dict[str, Any],
        execution: dict[str, Any],
        evaluation: dict[str, Any] | None,
    ) -> dict[str, Any]:
        task_fingerprint = sha256(task.encode("utf-8")).hexdigest()
        record = {
            "record_id": self._next_id,
            "task_fingerprint": task_fingerprint,
            "task_type": analysis.get("task_type"),
            "routed_model": routing.get("model"),
            "executed_model": execution.get("model"),
            "execution_status": execution.get("status"),
            "evaluation_score": evaluation.get("score") if evaluation else None,
            "attempts": execution.get("attempts", 0),
            "total_attempts": execution.get("total_attempts", 0),
            "budget_limit": execution.get("budget_limit"),
            "fallback_used": execution.get("fallback_used", False),
            "timestamp": datetime.now(timezone.utc).isoformat(),
        }

        self._next_id += 1
        self._records.append(record)

        if len(self._records) > self.max_records:
            self._records.pop(0)

        return dict(record)

    def recent(self, limit: int = 10) -> list[dict[str, Any]]:
        if limit < 1:
            raise ValueError("limit must be at least 1")

        return [dict(record) for record in self._records[-limit:]]

    @property
    def size(self) -> int:
        return len(self._records)


DEFAULT_OUTCOME_MEMORY = OutcomeMemory()
