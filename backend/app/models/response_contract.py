from typing import Any


class ModelResponseNormalizer:
    """Normalize model adapter output into a stable provider-independent response contract."""

    def normalize(self, result: Any, model_name: str) -> dict[str, Any]:
        if not isinstance(model_name, str) or not model_name.strip():
            raise ValueError("model_name must be a non-empty string")
        if not isinstance(result, dict):
            raise ValueError("model result must be a dictionary")

        text = result.get("text")
        if not isinstance(text, str) or not text.strip():
            raise ValueError("model result must contain non-empty text")

        model = result.get("model") or model_name
        provider = result.get("provider")
        if not isinstance(model, str) or not model.strip():
            raise ValueError("model metadata must be a non-empty string")
        if not isinstance(provider, str) or not provider.strip():
            raise ValueError("provider metadata must be a non-empty string")

        normalized: dict[str, Any] = {
            "text": text,
            "model": model,
            "provider": provider,
        }

        grounding = result.get("grounding")
        if grounding is not None:
            if not isinstance(grounding, dict):
                raise ValueError("grounding metadata must be a dictionary")
            normalized["grounding"] = dict(grounding)

        return normalized
