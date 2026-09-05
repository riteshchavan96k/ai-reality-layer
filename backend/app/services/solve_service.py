from backend.app.orchestrator.orchestrator import orchestrate_task


def process_task(task: str, human_approved: bool = False) -> dict:
    return orchestrate_task(task, human_approved=human_approved)
