from backend.app.analyzer.task_analyzer import analyze_task
from backend.app.router.model_router import route_task


def orchestrate_task(task: str) -> dict:
    analysis = analyze_task(task)
    routing = route_task(analysis["task_type"])

    return {
        "status": "orchestrated",
        "analysis": analysis,
        "routing": routing,
    }