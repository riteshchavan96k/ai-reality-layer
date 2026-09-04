from backend.app.models.catalog import get_available_models
from backend.app.router.model_selector import select_model
from backend.app.router.task_requirements import extract_requirements


def route_task(task: str, task_type: str) -> dict:
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

    return {
        "strategy": strategy,
        "requirements": requirements,
        "model": selection["selected_model"],
        "candidates": selection["candidates"],
        "scores": selection["scores"],
    }
