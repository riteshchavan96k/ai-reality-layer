from typing import Dict, List


MODEL_PROFILES = {
    "mock-model": {
        "programming": 1.0,
        "reasoning": 1.0,
        "long_context": 1.0,
        "general": 1.0,
    }
}


def select_model(strategy: str, candidates: List[str]) -> dict:
    scores: Dict[str, float] = {}

    for model in candidates:
        profile = MODEL_PROFILES.get(model, {})
        score = profile.get(strategy, 0.0)
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