from typing import Any, Callable

from backend.app.evaluation.response_evaluator import evaluate_response
from backend.app.execution.execution_budget import ExecutionBudget
from backend.app.execution.retry_policy import RetryPolicy


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
) -> dict[str, Any]:
    """Try alternative candidates when the initial response needs review and keep the best evaluation."""
    best = {
        "model": initial_execution.get("model"),
        "execution": initial_execution,
        "evaluation": initial_evaluation,
    }
    recovery_attempts = 0
    candidates_tried: list[str] = []

    if initial_evaluation["status"] == "pass":
        return {
            "used": False,
            "reason": "initial_evaluation_passed",
            "best": best,
            "recovery_attempts": 0,
            "candidates_tried": candidates_tried,
        }

    for model_name in candidates:
        if model_name == initial_execution.get("model"):
            continue
        if execution_budget.remaining_attempts <= 0:
            break

        adapter = adapter_resolver(model_name)
        if adapter is None:
            continue

        remaining = execution_budget.remaining_attempts
        model_policy = RetryPolicy(max_attempts=min(retry_policy.max_attempts, remaining))
        execution = model_policy.execute(lambda: adapter.generate(task))
        execution_budget.consume(execution["attempts"])
        recovery_attempts += execution["attempts"]
        candidates_tried.append(model_name)

        if execution["status"] != "success":
            continue

        evaluation = evaluate_response(
            task,
            execution["result"],
            analysis,
            {**routing, "model": model_name},
        )

        if evaluation["score"] > best["evaluation"]["score"]:
            best = {
                "model": model_name,
                "execution": {
                    **execution,
                    "model": model_name,
                    "total_attempts": execution_budget.used_attempts,
                    "budget_limit": execution_budget.max_attempts,
                },
                "evaluation": evaluation,
            }

        if evaluation["status"] == "pass":
            break

    improved = best["model"] != initial_execution.get("model")
    return {
        "used": bool(candidates_tried),
        "reason": "initial_evaluation_review",
        "improved": improved,
        "best": best,
        "recovery_attempts": recovery_attempts,
        "candidates_tried": candidates_tried,
    }
