from dataclasses import dataclass
from datetime import datetime
import re
from typing import Any, Mapping


_SHA256_RE = re.compile(r"^[0-9a-f]{64}$")


@dataclass(frozen=True)
class OutcomeMemoryRecord:
    """Canonical provider-neutral contract for one stored execution outcome."""

    record_id: int
    task_fingerprint: str
    task_type: str | None
    routed_model: str | None
    executed_model: str | None
    execution_status: str
    evaluation_score: int | float | None
    attempts: int
    total_attempts: int
    budget_limit: int | None
    fallback_used: bool
    timestamp: str

    @classmethod
    def validate(cls, raw: "OutcomeMemoryRecord | Mapping[str, Any]") -> "OutcomeMemoryRecord":
        if isinstance(raw, cls):
            values = raw
        else:
            if not isinstance(raw, Mapping):
                raise TypeError("outcome memory record must be a mapping or OutcomeMemoryRecord")
            required = {
                "record_id",
                "task_fingerprint",
                "task_type",
                "routed_model",
                "executed_model",
                "execution_status",
                "evaluation_score",
                "attempts",
                "total_attempts",
                "budget_limit",
                "fallback_used",
                "timestamp",
            }
            missing = sorted(required - set(raw))
            if missing:
                raise ValueError(f"outcome memory record missing fields: {', '.join(missing)}")
            values = cls(**{key: raw[key] for key in required})

        if not isinstance(values.record_id, int) or isinstance(values.record_id, bool) or values.record_id < 1:
            raise ValueError("record_id must be a positive integer")
        if not isinstance(values.task_fingerprint, str) or not _SHA256_RE.fullmatch(values.task_fingerprint):
            raise ValueError("task_fingerprint must be a lowercase SHA-256 hex digest")
        if values.execution_status not in {"success", "failed"}:
            raise ValueError("execution_status must be 'success' or 'failed'")
        if not isinstance(values.attempts, int) or isinstance(values.attempts, bool) or values.attempts < 0:
            raise ValueError("attempts must be a non-negative integer")
        if not isinstance(values.total_attempts, int) or isinstance(values.total_attempts, bool) or values.total_attempts < 0:
            raise ValueError("total_attempts must be a non-negative integer")
        if values.attempts > values.total_attempts:
            raise ValueError("attempts cannot exceed total_attempts")
        if values.budget_limit is not None and (
            not isinstance(values.budget_limit, int)
            or isinstance(values.budget_limit, bool)
            or values.budget_limit < 1
        ):
            raise ValueError("budget_limit must be a positive integer or None")
        if not isinstance(values.fallback_used, bool):
            raise ValueError("fallback_used must be a boolean")
        if values.evaluation_score is not None and (
            not isinstance(values.evaluation_score, (int, float))
            or isinstance(values.evaluation_score, bool)
        ):
            raise ValueError("evaluation_score must be numeric or None")
        if not isinstance(values.timestamp, str) or not values.timestamp.strip():
            raise ValueError("timestamp must be a non-empty ISO-8601 timestamp")
        try:
            parsed = datetime.fromisoformat(values.timestamp.replace("Z", "+00:00"))
        except ValueError as exc:
            raise ValueError("timestamp must be a valid ISO-8601 timestamp") from exc
        if parsed.tzinfo is None or parsed.utcoffset() is None:
            raise ValueError("timestamp must include timezone information")

        for field_name in ("task_type", "routed_model", "executed_model"):
            field_value = getattr(values, field_name)
            if field_value is not None and (not isinstance(field_value, str) or not field_value.strip()):
                raise ValueError(f"{field_name} must be a non-empty string or None")

        if values.execution_status == "success" and not values.executed_model:
            raise ValueError("successful execution outcome requires executed_model")

        return values

    def to_dict(self) -> dict[str, Any]:
        return {
            "record_id": self.record_id,
            "task_fingerprint": self.task_fingerprint,
            "task_type": self.task_type,
            "routed_model": self.routed_model,
            "executed_model": self.executed_model,
            "execution_status": self.execution_status,
            "evaluation_score": self.evaluation_score,
            "attempts": self.attempts,
            "total_attempts": self.total_attempts,
            "budget_limit": self.budget_limit,
            "fallback_used": self.fallback_used,
            "timestamp": self.timestamp,
        }


__all__ = ["OutcomeMemoryRecord"]
