from typing import Any


def evaluate_response(
    task: str,
    result: dict[str, Any],
    analysis: dict[str, Any],
    routing: dict[str, Any],
) -> dict[str, Any]:
    """Evaluate the structural quality of one model execution.

    This prototype intentionally evaluates observable execution signals rather
    than claiming semantic correctness. A later evaluator can add model-based,
    reference-based, or task-specific quality checks.
    """

    text = result.get("text")
    checks = {
        "non_empty_response": isinstance(text, str) and bool(text.strip()),
        "model_metadata_present": bool(result.get("model")),
        "provider_metadata_present": bool(result.get("provider")),
        "routing_available": bool(routing.get("model")),
        "task_analysis_available": bool(analysis.get("task_type")),
    }

    passed_checks = sum(checks.values())
    total_checks = len(checks)
    score = passed_checks / total_checks if total_checks else 0.0

    return {
        "score": score,
        "status": "pass" if score == 1.0 else "review",
        "checks": checks,
        "passed_checks": passed_checks,
        "total_checks": total_checks,
        "task": task,
        "limitation": "Prototype structural evaluation; semantic correctness is not yet measured.",
    }
