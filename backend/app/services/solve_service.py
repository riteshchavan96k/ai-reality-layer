from backend.app.orchestrator.orchestrator import orchestrate_task


def process_task(task: str) -> dict:
    return orchestrate_task(task)