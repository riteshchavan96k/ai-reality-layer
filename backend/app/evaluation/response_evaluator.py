from typing import Any

from backend.app.evaluation.relevance import evaluate_relevance


def evaluate_response(
    task: str,
    result: dict[str, Any],
    analysis: dict[str, Any],
    routing: dict[str, Any],
) -> dict[str, Any]:
    """Evaluate structural integrity plus reference-free task-response relevance."""

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
    structural_score = passed_checks / total_checks if total_checks else 0.0

    relevance = (
        evaluate_relevance(task, text)
        if isinstance(text, str)
        else {
            "score": 0.0,
            "status": "review",
            "task_terms": [],
            "matched_terms": [],
            "coverage": 0.0,
            "limitation": "Response text is unavailable for relevance evaluation.",
        }
    )

    score = (structural_score + relevance["score"]) / 2

    return {
        "score": score,
        "status": "pass" if score >= 0.8 else "review",
        "checks": checks,
        "passed_checks": passed_checks,
        "total_checks": total_checks,
        "structural_score": structural_score,
        "relevance": relevance,
        "task": task,
        "limitation": "Reference-free relevance is lexical and does not establish factual or semantic correctness.",
    }
