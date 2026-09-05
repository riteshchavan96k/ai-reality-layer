import os
import sqlite3
from datetime import datetime, timezone
from hashlib import sha256
from typing import Any


class PersistentOutcomeMemory:
    """SQLite-backed outcome memory with the same read interface as OutcomeMemory."""

    def __init__(self, database_path: str) -> None:
        if not database_path:
            raise ValueError("database_path must not be empty")

        self.database_path = database_path
        parent = os.path.dirname(os.path.abspath(database_path))
        os.makedirs(parent, exist_ok=True)
        self._initialize()

    def _connect(self) -> sqlite3.Connection:
        connection = sqlite3.connect(self.database_path)
        connection.row_factory = sqlite3.Row
        return connection

    def _initialize(self) -> None:
        with self._connect() as connection:
            connection.execute(
                """
                CREATE TABLE IF NOT EXISTS execution_outcomes (
                    record_id INTEGER PRIMARY KEY AUTOINCREMENT,
                    task_fingerprint TEXT NOT NULL,
                    task_type TEXT,
                    routed_model TEXT,
                    executed_model TEXT,
                    execution_status TEXT NOT NULL,
                    evaluation_score REAL,
                    attempts INTEGER NOT NULL,
                    total_attempts INTEGER NOT NULL,
                    budget_limit INTEGER,
                    fallback_used INTEGER NOT NULL,
                    timestamp TEXT NOT NULL
                )
                """
            )
            connection.commit()

    @staticmethod
    def _record_from_row(row: sqlite3.Row) -> dict[str, Any]:
        record = dict(row)
        record["fallback_used"] = bool(record["fallback_used"])
        return record

    def record(
        self,
        task: str,
        analysis: dict[str, Any],
        routing: dict[str, Any],
        execution: dict[str, Any],
        evaluation: dict[str, Any] | None,
    ) -> dict[str, Any]:
        task_fingerprint = sha256(task.encode("utf-8")).hexdigest()
        timestamp = datetime.now(timezone.utc).isoformat()

        with self._connect() as connection:
            cursor = connection.execute(
                """
                INSERT INTO execution_outcomes (
                    task_fingerprint,
                    task_type,
                    routed_model,
                    executed_model,
                    execution_status,
                    evaluation_score,
                    attempts,
                    total_attempts,
                    budget_limit,
                    fallback_used,
                    timestamp
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    task_fingerprint,
                    analysis.get("task_type"),
                    routing.get("model"),
                    execution.get("model"),
                    execution.get("status"),
                    evaluation.get("score") if evaluation else None,
                    execution.get("attempts", 0),
                    execution.get("total_attempts", 0),
                    execution.get("budget_limit"),
                    int(bool(execution.get("fallback_used", False))),
                    timestamp,
                ),
            )
            record_id = cursor.lastrowid
            connection.commit()

        return {
            "record_id": record_id,
            "task_fingerprint": task_fingerprint,
            "task_type": analysis.get("task_type"),
            "routed_model": routing.get("model"),
            "executed_model": execution.get("model"),
            "execution_status": execution.get("status"),
            "evaluation_score": evaluation.get("score") if evaluation else None,
            "attempts": execution.get("attempts", 0),
            "total_attempts": execution.get("total_attempts", 0),
            "budget_limit": execution.get("budget_limit"),
            "fallback_used": bool(execution.get("fallback_used", False)),
            "timestamp": timestamp,
        }

    def recent(self, limit: int = 10) -> list[dict[str, Any]]:
        if limit < 1:
            raise ValueError("limit must be at least 1")

        with self._connect() as connection:
            rows = connection.execute(
                "SELECT * FROM execution_outcomes ORDER BY record_id DESC LIMIT ?",
                (limit,),
            ).fetchall()

        return [self._record_from_row(row) for row in reversed(rows)]

    def statistics(self) -> dict[str, Any]:
        with self._connect() as connection:
            rows = connection.execute(
                "SELECT * FROM execution_outcomes ORDER BY record_id ASC"
            ).fetchall()

        records = [self._record_from_row(row) for row in rows]
        total = len(records)
        successful = sum(record["execution_status"] == "success" for record in records)
        failed = sum(record["execution_status"] == "failed" for record in records)
        scored = [
            record["evaluation_score"]
            for record in records
            if isinstance(record["evaluation_score"], (int, float))
        ]
        attempts = [record["total_attempts"] for record in records]
        fallback_count = sum(record["fallback_used"] for record in records)

        by_model: dict[str, dict[str, Any]] = {}
        for record in records:
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
            model_stats["success_rate"] = model_stats["successful"] / executions
            model_stats["average_score"] = sum(scores) / len(scores) if scores else None
            model_stats["average_attempts"] = model_stats["total_attempts"] / executions

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

    def routing_signals(self, task_type: str) -> dict[str, dict[str, Any]]:
        with self._connect() as connection:
            rows = connection.execute(
                "SELECT * FROM execution_outcomes WHERE task_type = ? ORDER BY record_id ASC",
                (task_type,),
            ).fetchall()

        signals: dict[str, dict[str, Any]] = {}
        for row in rows:
            record = self._record_from_row(row)
            model = record["executed_model"]
            if not model:
                continue
            model_stats = signals.setdefault(
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

        for model_stats in signals.values():
            executions = model_stats["executions"]
            scores = model_stats.pop("scores")
            model_stats["success_rate"] = model_stats["successful"] / executions
            model_stats["average_score"] = sum(scores) / len(scores) if scores else None
            model_stats["average_attempts"] = model_stats["total_attempts"] / executions

        return signals

    @property
    def size(self) -> int:
        with self._connect() as connection:
            row = connection.execute("SELECT COUNT(*) AS count FROM execution_outcomes").fetchone()
        return int(row["count"])
