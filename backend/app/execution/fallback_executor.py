from typing import Any, Callable

from backend.app.execution.execution_budget import ExecutionBudget
from backend.app.execution.retry_policy import RetryPolicy


def execute_with_fallback(
    task: str,
    model_names: list[str],
    adapter_resolver: Callable[[str], Any],
    retry_policy: RetryPolicy,
    execution_budget: ExecutionBudget | None = None,
    context: dict[str, Any] | None = None,
) -> dict:
    """Try candidate models in order while respecting a total attempt budget."""
    attempts_by_model: dict[str, int] = {}
    errors: dict[str, str] = {}
    budget = execution_budget or ExecutionBudget(
        max_attempts=retry_policy.max_attempts * max(len(model_names), 1)
    )

    for model_name in model_names:
        adapter = adapter_resolver(model_name)

        if adapter is None:
            errors[model_name] = "Model not available"
            attempts_by_model[model_name] = 0
            continue

        remaining = budget.remaining_attempts
        if remaining <= 0:
            break

        model_policy = RetryPolicy(
            max_attempts=min(retry_policy.max_attempts, remaining)
        )
        execution = model_policy.execute(lambda: adapter.generate(task, context=context))
        budget.consume(execution["attempts"])
        attempts_by_model[model_name] = execution["attempts"]

        if execution["status"] == "success":
            return {
                "status": "success",
                "model": model_name,
                "attempts": execution["attempts"],
                "total_attempts": budget.used_attempts,
                "budget_limit": budget.max_attempts,
                "attempts_by_model": attempts_by_model,
                "fallback_used": bool(errors),
                "result": execution["result"],
            }

        errors[model_name] = execution["error"]

    return {
        "status": "failed",
        "model": None,
        "attempts": sum(attempts_by_model.values()),
        "total_attempts": budget.used_attempts,
        "budget_limit": budget.max_attempts,
        "attempts_by_model": attempts_by_model,
        "fallback_used": len(model_names) > 1,
        "errors": errors,
    }
