from typing import Dict, List

from backend.app.models.catalog import MODEL_CATALOG


def select_model(requirements: List[str], candidates: List[str]) -> dict:
    scores: Dict[str, float] = {}

    for model in candidates:
        profile = MODEL_CATALOG.get(model, {})
        capabilities = profile.get("capabilities", [])

        if requirements:
            matched_requirements = sum(
                1 for requirement in requirements if requirement in capabilities
            )
            score = matched_requirements / len(requirements)
        else:
            score = 0.0

        scores[model] = score

    if not scores:
        return {
            "selected_model": None,
            "candidates": candidates,
            "scores": scores,
        }

    selected_model = max(scores, key=scores.get)

    return {
        "selected_model": selected_model,
        "candidates": candidates,
        "scores": scores,
    }
