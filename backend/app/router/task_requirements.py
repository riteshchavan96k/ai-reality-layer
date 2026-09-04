def extract_requirements(task: str) -> list[str]:
    normalized_task = task.lower()

    requirements = []

    if (
        "python" in normalized_task
        or "code" in normalized_task
        or "program" in normalized_task
        or "programming" in normalized_task
    ):
        requirements.append("programming")

    if (
        "solve" in normalized_task
        or "equation" in normalized_task
        or "calculate" in normalized_task
        or "math" in normalized_task
        or "mathematical" in normalized_task
        or "mathematics" in normalized_task
        or "reason" in normalized_task
    ):
        requirements.append("reasoning")

    if (
        "summarize" in normalized_task
        or "summary" in normalized_task
        or "summarise" in normalized_task
    ):
        requirements.append("long_context")

    if not requirements:
        requirements.append("general")

    return requirements
