import inspect
from typing import Any, Callable

from backend.app.evaluation.response_evaluator import evaluate_response
from backend.app.evaluation.response_evaluation_normalizer import (
    ResponseEvaluationResultNormalizer,
)
from backend.app.evaluation.quality_recovery_normalizer import (
    QualityRecoveryResultNormalizer,
)
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


def _seed_attempts_by_model(
    initial_execution: dict[str, Any],
    execution_budget: ExecutionBudget,
) -> dict[str, int]:
    """Seed canonical attempt accounting from the shared execution budget."""
    raw_attempts = initial_execution.get("attempts_by_model")
    if isinstance(raw_attempts, dict):
        valid = all(
            isinstance(name, str)
            and bool(name.strip())
            and type(count) is int
            and count >= 0
            for name, count in raw_attempts.items()
        )
        if valid and sum(raw_attempts.values()) == execution_budget.used_attempts:
            return dict(raw_attempts)

    if execution_budget.used_attempts == 0:
        return {}

    initial_model = initial_execution.get("model")
    if isinstance(initial_model, str) and initial_model.strip():
        return {initial_model: execution_budget.used_attempts}

    raise ValueError("cannot establish canonical recovery attempt accounting")


def _canonical_recovery_execution(
    *,
    model_name: str,
    attempts: int,
    attempts_by_model: dict[str, int],
    execution_budget: ExecutionBudget,
    initial_execution: dict[str, Any],
    result: dict[str, Any],
) -> dict[str, Any]:
    """Build a recovery success through the canonical model-execution contract."""
    return ModelExecutionResultNormalizer.normalize(
        ModelExecutionResult(
            status="success",
            model=model_name,
            attempts=attempts,
            total_attempts=execution_budget.used_attempts,
            budget_limit=execution_budget.max_attempts,
            attempts_by_model=dict(attempts_by_model),
            fallback_used=bool(
                initial_execution.get("fallback_used", False)
                or model_name != initial_execution.get("model")
            ),
            result=result,
        )
    ).to_dict()


def recover_with_evaluation(
    task: str,
    candidates: list[str],
    adapter_resolver: Callable[[str], Any],
    analysis: dict[str, Any],
    routing: dict[str, Any],
    initial_execution: dict[str, Any],
    initial_evaluation: dict[str, Any],
    retry_policy: RetryPolicy,
    execution_budget: ExecutionBudget,
    context: dict[str, Any] | None = None,
    provider_name_resolver: Callable[[str], str | None] | None = None,
    invocation_executor: Callable[[str, str, str, dict[str, Any] | None], dict[str, Any]] | None = None,
) -> dict[str, Any]:
    """Try alternative candidates when the initial response needs review and keep the best evaluation.

    When an invocation executor is supplied, recovery uses the same provider-neutral
    execution/result boundary as the primary execution path. The legacy adapter path
    remains available for isolated callers and regression compatibility.
    """
    initial_evaluation = ResponseEvaluationResultNormalizer.normalize(
        initial_evaluation
    ).to_dict()
    best = {
        "model": initial_execution.get("model"),
        "execution": initial_execution,
        "evaluation": initial_evaluation,
    }
    recovery_attempts = 0
    candidates_tried: list[str] = []
    normalizer = ModelResponseNormalizer()

    if initial_evaluation["status"] == "pass":
        return QualityRecoveryResultNormalizer.normalize(
            {
                "used": False,
                "reason": "initial_evaluation_passed",
                "improved": False,
                "best": best,
                "recovery_attempts": 0,
                "candidates_tried": candidates_tried,
            }
        ).to_dict()

    attempts_by_model = _seed_attempts_by_model(initial_execution, execution_budget)

    for model_name in candidates:
        if model_name == initial_execution.get("model"):
            continue
        if execution_budget.remaining_attempts <= 0:
            break

        if invocation_executor is not None:
            if provider_name_resolver is None:
                raise ValueError("provider_name_resolver is required with invocation_executor")

            provider_name = provider_name_resolver(model_name)
            if not provider_name:
                continue

            attempts = 0
            execution_result = None
            last_reason = None

            while attempts < retry_policy.max_attempts and execution_budget.remaining_attempts > 0:
                provider_result = invocation_executor(
                    provider_name,
                    model_name,
                    task,
                    context,
                )

                if provider_result["status"] == "blocked":
                    break

                attempts += 1
                execution_budget.consume(1)
                attempts_by_model[model_name] = attempts_by_model.get(model_name, 0) + 1

                if provider_result["status"] == "completed":
                    execution_result = _canonical_recovery_execution(
                        model_name=model_name,
                        attempts=attempts,
                        attempts_by_model=attempts_by_model,
                        execution_budget=execution_budget,
                        initial_execution=initial_execution,
                        result=provider_result["result"],
                    )
                    break

                last_reason = provider_result.get(
                    "reason",
                    "provider_execution_failed",
                )

            recovery_attempts += attempts

            if attempts == 0:
                continue

            candidates_tried.append(model_name)

            if execution_result is None:
                continue

            evaluation = ResponseEvaluationResultNormalizer.normalize(
                evaluate_response(
                    task,
                    execution_result["result"],
                    analysis,
                    {**routing, "model": model_name},
                )
            ).to_dict()

            if evaluation["score"] > best["evaluation"]["score"]:
                best = {
                    "model": model_name,
                    "execution": execution_result,
                    "evaluation": evaluation,
                }

            if evaluation["status"] == "pass":
                break

            continue

        adapter = adapter_resolver(model_name)
        if adapter is None:
            continue

        remaining = execution_budget.remaining_attempts
        model_policy = RetryPolicy(max_attempts=min(retry_policy.max_attempts, remaining))
        execution = model_policy.execute(
            lambda: normalizer.normalize(
                _invoke_adapter_generate(adapter, task, context),
                model_name,
            )
        )
        execution_budget.consume(execution["attempts"])
        recovery_attempts += execution["attempts"]
        attempts_by_model[model_name] = (
            attempts_by_model.get(model_name, 0) + execution["attempts"]
        )
        candidates_tried.append(model_name)

        if execution["status"] != "success":
            continue

        canonical_execution = _canonical_recovery_execution(
            model_name=model_name,
            attempts=execution["attempts"],
            attempts_by_model=attempts_by_model,
            execution_budget=execution_budget,
            initial_execution=initial_execution,
            result=execution["result"],
        )

        evaluation = ResponseEvaluationResultNormalizer.normalize(
            evaluate_response(
                task,
                canonical_execution["result"],
                analysis,
                {**routing, "model": model_name},
            )
        ).to_dict()

        if evaluation["score"] > best["evaluation"]["score"]:
            best = {
                "model": model_name,
                "execution": canonical_execution,
                "evaluation": evaluation,
            }

        if evaluation["status"] == "pass":
            break

    improved = best["model"] != initial_execution.get("model")
    return QualityRecoveryResultNormalizer.normalize(
        {
            "used": bool(candidates_tried),
            "reason": "initial_evaluation_review",
            "improved": improved,
            "best": best,
            "recovery_attempts": recovery_attempts,
            "candidates_tried": candidates_tried,
        }
    ).to_dict()
