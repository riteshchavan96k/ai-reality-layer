from backend.app.analyzer.task_analyzer import analyze_task
from backend.app.router.model_router import route_task
from backend.app.models.registry import get_model_adapter


def orchestrate_task(task: str) -> dict:
    analysis = analyze_task(task)
    routing = route_task(analysis["task_type"])

    model = get_model_adapter("mock-model")

    if model is None:
        return {
            "status": "error",
            "message": "Model not available",
        }

    result = model.generate(task)

    return {
        "status": "orchestrated",
        "analysis": analysis,
        "routing": routing,
        "result": result,
    }