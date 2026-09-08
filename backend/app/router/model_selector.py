from typing import Dict, List

from backend.app.models.catalog import MODEL_CATALOG
from backend.app.models.capability_contract import ModelCapabilityContract


_CAPABILITY_CONTRACT = ModelCapabilityContract()


def select_model(requirements: List[str], candidates: List[str]) -> dict:
    scores: Dict[str, float] = {}
    catalog = _CAPABILITY_CONTRACT.normalize_catalog(MODEL_CATALOG)

    for model in candidates:
        profile = catalog.get(model)
        if profile is None:
            scores[model] = 0.0
            continue

        capabilities = profile["capabilities"]

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
