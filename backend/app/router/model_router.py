from backend.app.models.catalog import get_available_models
from backend.app.router.model_selector import select_model
from backend.app.router.task_requirements import extract_requirements
from backend.app.router.routing_optimizer import AdaptiveRoutingOptimizer
from backend.app.execution.outcome_memory import OutcomeMemory


def route_task(
    task: str,
    task_type: str,
    outcome_memory: OutcomeMemory | None = None,
    routing_optimizer: AdaptiveRoutingOptimizer | None = None,
) -> dict:
    if task_type == "programming":
        strategy = "programming"
    elif task_type == "mathematics":
        strategy = "reasoning"
    elif task_type == "summarization":
        strategy = "long_context"
    else:
        strategy = "general"

    requirements = extract_requirements(task)
    candidates = get_available_models()

    selection = select_model(requirements, candidates)
    routing = {
        "strategy": strategy,
        "requirements": requirements,
        "model": selection["selected_model"],
        "candidates": selection["candidates"],
        "scores": selection["scores"],
    }

    if outcome_memory is None:
        routing["optimization"] = {
            "ranked_models": [],
            "selected_model": routing["model"],
            "exploration": True,
            "min_samples": 2,
            "status": "no_history",
        }
        return routing

    optimizer = routing_optimizer or AdaptiveRoutingOptimizer()
    optimization = optimizer.rank(task_type, candidates, outcome_memory)

    if optimization["selected_model"] is not None:
        routing["model"] = optimization["selected_model"]
        routing["candidates"] = [
            item["model"] for item in optimization["ranked_models"]
        ]
        routing["scores"] = {
            item["model"]: item["score"] for item in optimization["ranked_models"]
        }

    routing["optimization"] = {
        **optimization,
        "status": "exploring" if optimization["exploration"] else "optimized",
    }
    return routing
