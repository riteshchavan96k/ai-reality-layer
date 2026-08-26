def route_task(task_type: str) -> dict:
    if task_type == "programming":
        strategy = "programming"
    elif task_type == "mathematics":
        strategy = "reasoning"
    elif task_type == "summarization":
        strategy = "long_context"
    else:
        strategy = "general"

    return {
        "strategy": strategy,
    }