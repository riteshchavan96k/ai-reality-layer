from dataclasses import dataclass
from typing import Any


@dataclass(frozen=True)
class ModelExecutionResult:
    """Canonical provider-neutral outcome for model execution."""

    status: str
    model: str | None
    attempts: int
    total_attempts: int
    budget_limit: int
    attempts_by_model: dict[str, int]
    fallback_used: bool
    result: dict[str, Any] | None = None
    errors: dict[str, str] | None = None

    def __post_init__(self) -> None:
        if self.status not in {"success", "failed"}:
            raise ValueError("status must be success or failed")
        if self.status == "success":
            if not isinstance(self.model, str) or not self.model.strip():
                raise ValueError("successful execution requires a model")
            if not isinstance(self.result, dict):
                raise ValueError("successful execution requires a result mapping")
            if self.errors:
                raise ValueError("successful execution cannot contain errors")
        else:
            if self.model is not None:
                raise ValueError("failed execution cannot contain a model")
            if self.result is not None:
                raise ValueError("failed execution cannot contain a result")
            if not isinstance(self.errors, dict):
                raise ValueError("failed execution requires an errors mapping")
        for value, name in (
            (self.attempts, "attempts"),
            (self.total_attempts, "total_attempts"),
            (self.budget_limit, "budget_limit"),
        ):
            if not isinstance(value, int) or value < 0:
                raise ValueError(f"{name} must be a non-negative integer")
        if self.budget_limit < 1:
            raise ValueError("budget_limit must be at least 1")
        if self.attempts > self.total_attempts:
            raise ValueError("attempts cannot exceed total_attempts")
        if self.total_attempts > self.budget_limit:
            raise ValueError("total_attempts cannot exceed budget_limit")
        if not isinstance(self.attempts_by_model, dict) or any(
            not isinstance(name, str) or not name.strip() or not isinstance(count, int) or count < 0
            for name, count in self.attempts_by_model.items()
        ):
            raise ValueError("attempts_by_model must map non-empty model names to non-negative integers")
        if sum(self.attempts_by_model.values()) != self.total_attempts:
            raise ValueError("attempts_by_model counts must equal total_attempts")
        if not isinstance(self.fallback_used, bool):
            raise ValueError("fallback_used must be a boolean")

    @classmethod
    def validate(cls, raw_result: object) -> "ModelExecutionResult":
        if isinstance(raw_result, cls):
            return raw_result
        if not isinstance(raw_result, dict):
            raise ValueError("model execution result must be a mapping or ModelExecutionResult")
        required = {
            "status", "model", "attempts", "total_attempts", "budget_limit",
            "attempts_by_model", "fallback_used", "result", "errors",
        }
        missing = sorted(required - set(raw_result))
        if missing:
            raise ValueError(f"missing required fields: {', '.join(missing)}")
        attempts_by_model = raw_result["attempts_by_model"]
        if not isinstance(attempts_by_model, dict):
            raise ValueError("attempts_by_model must be a mapping")
        errors = raw_result["errors"]
        if errors is not None and not isinstance(errors, dict):
            raise ValueError("errors must be a mapping or None")
        result = raw_result["result"]
        if result is not None and not isinstance(result, dict):
            raise ValueError("result must be a mapping or None")
        return cls(
            status=raw_result["status"],
            model=raw_result["model"],
            attempts=raw_result["attempts"],
            total_attempts=raw_result["total_attempts"],
            budget_limit=raw_result["budget_limit"],
            attempts_by_model=dict(attempts_by_model),
            fallback_used=raw_result["fallback_used"],
            result=dict(result) if result is not None else None,
            errors=dict(errors) if errors is not None else None,
        )

    def to_dict(self) -> dict[str, Any]:
        return {
            "status": self.status,
            "model": self.model,
            "attempts": self.attempts,
            "total_attempts": self.total_attempts,
            "budget_limit": self.budget_limit,
            "attempts_by_model": dict(self.attempts_by_model),
            "fallback_used": self.fallback_used,
            "result": dict(self.result) if self.result is not None else None,
            "errors": dict(self.errors) if self.errors is not None else None,
        }


__all__ = ["ModelExecutionResult"]
