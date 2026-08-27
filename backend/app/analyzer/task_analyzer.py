def analyze_task(task: str) -> dict:
    normalized_task = task.lower()

    if "python" in normalized_task or "code" in normalized_task:
        task_type = "programming"

    elif (
        "equation" in normalized_task
        or "calculate" in normalized_task
        or "math" in normalized_task
        or "mathematical" in normalized_task
        or "mathematics" in normalized_task
        or "solve" in normalized_task
    ):
        task_type = "mathematics"

    elif "summarize" in normalized_task or "summary" in normalized_task:
        task_type = "summarization"

    else:
        task_type = "general"

    return {
        "task": task,
        "task_type": task_type,
        "confidence": 0.5,
    }