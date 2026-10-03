import inspect
from typing import Any, Callable

from backend.app.execution.execution_budget import ExecutionBudget
from backend.app.execution.model_execution_contract import ModelExecutionResult
from backend.app.execution.model_execution_normalizer import ModelExecutionResultNormalizer
from backend.app.execution.retry_policy import RetryPolicy
from backend.app.models.response_contract import ModelResponseNormalizer


def _invoke_adapter_generate(
    adapter: Any,
    task: str,
    context: dict[str, Any] | None,
) -> Any:
    """Invoke current or legacy adapter signatures without masking adapter errors."""
    generate = adapter.generate
    try:
        parameters = inspect.signature(generate).parameters.values()
    except (TypeError, ValueError):
        return generate(task, context=context)

    accepts_context = any(
        parameter.name == "context"
        or parameter.kind is inspect.Parameter.VAR_KEYWORD
        for parameter in parameters
    )
    if accepts_context:
        return generate(task, context=context)
    return generate(task)


def execute_with_fallback(
    task: str,
    model_names: list[str],
    adapter_resolver: Callable[[str], Any],
    retry_policy: RetryPolicy,
    execution_budget: ExecutionBudget | None = None,
    context: dict[str, Any] | None = None,
    provider_name_resolver: Callable[[str], str] | None = None,
    invocation_executor: Callable[[str, str, str, dict[str, Any] | None], dict[str, Any]] | None = None,
) -> dict:
    """Try candidate models in order while respecting a total attempt budget."""
    attempts_by_model: dict[str, int] = {}
    errors: dict[str, str] = {}
    budget = execution_budget or ExecutionBudget(
        max_attempts=retry_policy.max_attempts * max(len(model_names), 1)
    )
    normalizer = ModelResponseNormalizer()

    for model_name in model_names:
        if invocation_executor is not None:
            if provider_name_resolver is None:
                raise ValueError("provider_name_resolver is required with invocation_executor")

            provider_name = provider_name_resolver(model_name)
            if not provider_name:
                errors[model_name] = "Provider unavailable"
                attempts_by_model[model_name] = 0
                continue

            attempts = 0
            last_error = None

            while attempts < retry_policy.max_attempts and budget.remaining_attempts > 0:
                result = invocation_executor(provider_name, model_name, task, context)

                if result["status"] == "blocked":
                    attempts_by_model[model_name] = attempts
                    errors[model_name] = result.get("reason", "provider_execution_blocked")
                    break

                attempts += 1
                budget.consume(1)

                if result["status"] == "completed":
                    attempts_by_model[model_name] = attempts
                    return ModelExecutionResultNormalizer.normalize(
                        ModelExecutionResult(
                            status="success",
                            model=model_name,
                            attempts=attempts,
                            total_attempts=budget.used_attempts,
                            budget_limit=budget.max_attempts,
                            attempts_by_model=dict(attempts_by_model),
                            fallback_used=bool(errors),
                            result=result["result"],
                        )
                    ).to_dict()

                last_error = result.get("reason", "provider_execution_failed")

            attempts_by_model[model_name] = attempts
            if last_error is not None:
                errors[model_name] = last_error
            continue

        adapter = adapter_resolver(model_name)

        if adapter is None:
            errors[model_name] = "Model not available"
            attempts_by_model[model_name] = 0
            continue

        remaining = budget.remaining_attempts
        if remaining <= 0:
            break

        model_policy = RetryPolicy(max_attempts=min(retry_policy.max_attempts, remaining))
        execution = model_policy.execute(
            lambda: normalizer.normalize(
                _invoke_adapter_generate(adapter, task, context),
                model_name,
            )
        )
        budget.consume(execution["attempts"])
        attempts_by_model[model_name] = execution["attempts"]

        if execution["status"] == "success":
            return ModelExecutionResultNormalizer.normalize(
                ModelExecutionResult(
                    status="success",
                    model=model_name,
                    attempts=execution["attempts"],
                    total_attempts=budget.used_attempts,
                    budget_limit=budget.max_attempts,
                    attempts_by_model=dict(attempts_by_model),
                    fallback_used=bool(errors),
                    result=execution["result"],
                )
            ).to_dict()

        errors[model_name] = execution["error"]

    return ModelExecutionResultNormalizer.normalize(
        ModelExecutionResult(
            status="failed",
            model=None,
            attempts=sum(attempts_by_model.values()),
            total_attempts=budget.used_attempts,
            budget_limit=budget.max_attempts,
            attempts_by_model=dict(attempts_by_model),
            fallback_used=len(model_names) > 1,
            errors=dict(errors),
        )
    ).to_dict()
