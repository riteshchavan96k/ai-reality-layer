from backend.app.models.catalog import get_available_models
from backend.app.router.model_selector import select_model


def route_task(task_type: str) -> dict:
    if task_type == "programming":
        strategy = "programming"
    elif task_type == "mathematics":
        strategy = "reasoning"
    elif task_type == "summarization":
        strategy = "long_context"
    else:
        strategy = "general"

    candidates = get_available_models()

    selection = select_model(strategy, candidates)

    return {
        "strategy": strategy,
        "model": selection["selected_model"],
        "candidates": selection["candidates"],
        "scores": selection["scores"],
    }