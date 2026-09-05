from typing import Any

from backend.app.evaluation.response_evaluator import evaluate_response
from backend.app.orchestrator.orchestrator import orchestrate_task


BENCHMARK_CASES = [
    {"name": "general", "task": "Tell me about artificial intelligence"},
    {"name": "programming", "task": "Write Python code to reverse a string"},
    {"name": "mathematics", "task": "Solve this mathematics equation"},
    {"name": "summarization", "task": "Summarize the following document"},
]


def run_benchmark() -> dict[str, Any]:
    """Run the deterministic prototype benchmark suite."""

    results = []

    for case in BENCHMARK_CASES:
        orchestration = orchestrate_task(case["task"], human_approved=True)

        if orchestration.get("status") != "orchestrated":
            results.append(
                {
                    "name": case["name"],
                    "status": "failed",
                    "score": 0.0,
                    "orchestration_status": orchestration.get("status"),
                }
            )
            continue

        evaluation = orchestration.get("evaluation", {})
        results.append(
            {
                "name": case["name"],
                "status": evaluation.get("status", "review"),
                "score": evaluation.get("score", 0.0),
            }
        )

    scores = [item["score"] for item in results]
    average_score = sum(scores) / len(scores) if scores else 0.0
    passed = sum(1 for item in results if item["status"] == "pass")
    pass_rate = passed / len(results) if results else 0.0

    return {
        "benchmark": "prototype-v1",
        "cases": results,
        "case_count": len(results),
        "average_score": average_score,
        "pass_rate": pass_rate,
        "limitation": "Prototype benchmark measures structural execution quality, not semantic correctness.",
    }
