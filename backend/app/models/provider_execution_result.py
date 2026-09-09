from typing import Any

from backend.app.models.response_contract import ModelResponseNormalizer


class ProviderExecutionResultContract:
    """Normalize provider execution outcomes into a stable result envelope."""

    def __init__(self, response_normalizer: ModelResponseNormalizer | None = None):
        self._response_normalizer = response_normalizer or ModelResponseNormalizer()

    def completed(self, result: Any, model_name: str) -> dict[str, Any]:
        """Normalize a successful adapter response using the existing model contract."""
        normalized = self._response_normalizer.normalize(result, model_name)
        return {
            "status": "completed",
            "execution_performed": True,
            "result": normalized,
        }

    def failed(
        self,
        provider_name: str,
        model_name: str,
        request: dict[str, Any],
        reason: str = "provider_execution_failed",
    ) -> dict[str, Any]:
        """Return stable failure metadata without exposing exception details."""
        if not isinstance(provider_name, str) or not provider_name.strip():
            raise ValueError("provider_name must be a non-empty string")
        if not isinstance(model_name, str) or not model_name.strip():
            raise ValueError("model_name must be a non-empty string")
        if not isinstance(request, dict):
            raise ValueError("request must be a dictionary")
        if not isinstance(reason, str) or not reason.strip():
            raise ValueError("reason must be a non-empty string")

        return {
            "status": "failed",
            "execution_performed": True,
            "provider": provider_name,
            "model": model_name,
            "reason": reason,
            "request": dict(request),
        }

    def blocked(
        self,
        provider_name: str,
        model_name: str,
        request: dict[str, Any],
        reason: str = "model_adapter_unavailable",
    ) -> dict[str, Any]:
        """Return a stable non-execution result for a blocked invocation."""
        if not isinstance(provider_name, str) or not provider_name.strip():
            raise ValueError("provider_name must be a non-empty string")
        if not isinstance(model_name, str) or not model_name.strip():
            raise ValueError("model_name must be a non-empty string")
        if not isinstance(request, dict):
            raise ValueError("request must be a dictionary")
        if not isinstance(reason, str) or not reason.strip():
            raise ValueError("reason must be a non-empty string")

        return {
            "status": "blocked",
            "execution_performed": False,
            "provider": provider_name,
            "model": model_name,
            "reason": reason,
            "request": dict(request),
        }
