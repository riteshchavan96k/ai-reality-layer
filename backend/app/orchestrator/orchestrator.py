from backend.app.analyzer.task_analyzer import analyze_task


def orchestrate_task(task: str) -> dict:
    analysis = analyze_task(task)

    return {
        "status": "orchestrated",
        "analysis": analysis,
    }