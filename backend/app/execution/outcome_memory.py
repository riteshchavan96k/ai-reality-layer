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

    def statistics(self) -> dict[str, Any]:
        """Return aggregate outcome signals without exposing raw task text."""
        total = len(self._records)
        successful = sum(
            1 for record in self._records if record["execution_status"] == "success"
        )
        failed = sum(
            1 for record in self._records if record["execution_status"] == "failed"
        )
        scored = [
            record["evaluation_score"]
            for record in self._records
            if isinstance(record["evaluation_score"], (int, float))
        ]
        attempts = [record["total_attempts"] for record in self._records]
        fallback_count = sum(
            1 for record in self._records if record["fallback_used"]
        )

        by_model: dict[str, dict[str, Any]] = {}
        for record in self._records:
            model = record["executed_model"]
            if not model:
                continue

            model_stats = by_model.setdefault(
                model,
                {
                    "executions": 0,
                    "successful": 0,
                    "failed": 0,
                    "scores": [],
                    "total_attempts": 0,
                },
            )
            model_stats["executions"] += 1
            model_stats["successful"] += record["execution_status"] == "success"
            model_stats["failed"] += record["execution_status"] == "failed"
            model_stats["total_attempts"] += record["total_attempts"]
            if isinstance(record["evaluation_score"], (int, float)):
                model_stats["scores"].append(record["evaluation_score"])

        for model_stats in by_model.values():
            executions = model_stats["executions"]
            scores = model_stats.pop("scores")
            model_stats["success_rate"] = (
                model_stats["successful"] / executions if executions else 0.0
            )
            model_stats["average_score"] = (
                sum(scores) / len(scores) if scores else None
            )
            model_stats["average_attempts"] = (
                model_stats["total_attempts"] / executions if executions else 0.0
            )

        return {
            "total_records": total,
            "successful": successful,
            "failed": failed,
            "success_rate": successful / total if total else 0.0,
            "average_score": sum(scored) / len(scored) if scored else None,
            "average_attempts": sum(attempts) / len(attempts) if attempts else 0.0,
            "fallback_rate": fallback_count / total if total else 0.0,
            "by_model": by_model,
        }

    @property
    def size(self) -> int:
        return len(self._records)


DEFAULT_OUTCOME_MEMORY = OutcomeMemory()
