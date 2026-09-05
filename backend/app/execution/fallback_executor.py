from typing import Any, Callable

from backend.app.execution.retry_policy import RetryPolicy


def execute_with_fallback(
    task: str,
    model_names: list[str],
    adapter_resolver: Callable[[str], Any],
    retry_policy: RetryPolicy,
) -> dict:
    """Try candidate models in order, retrying each before falling back."""
    attempts_by_model: dict[str, int] = {}
    errors: dict[str, str] = {}

    for model_name in model_names:
        adapter = adapter_resolver(model_name)

        if adapter is None:
            errors[model_name] = "Model not available"
            attempts_by_model[model_name] = 0
            continue

        execution = retry_policy.execute(lambda: adapter.generate(task))
        attempts_by_model[model_name] = execution["attempts"]

        if execution["status"] == "success":
            return {
                "status": "success",
                "model": model_name,
                "attempts": execution["attempts"],
                "attempts_by_model": attempts_by_model,
                "fallback_used": bool(errors),
                "result": execution["result"],
            }

        errors[model_name] = execution["error"]

    return {
        "status": "failed",
        "model": None,
        "attempts": sum(attempts_by_model.values()),
        "attempts_by_model": attempts_by_model,
        "fallback_used": len(model_names) > 1,
        "errors": errors,
    }
