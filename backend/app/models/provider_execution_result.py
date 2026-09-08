from typing import Any

from backend.app.models.response_contract import ModelResponseNormalizer


class ProviderExecutionResultContract:
    """Normalize provider execution outcomes into a stable result envelope."""

    def __init__(self, response_normalizer: ModelResponseNormalizer | None = None):
        self._response_normalizer = response_normalizer or ModelResponseNormalizer()

    def normalize(self, execution: Any, model_name: str) -> dict[str, Any]:
        if not isinstance(model_name, str) or not model_name.strip():
            raise ValueError("model_name must be a non-empty string")
        if not isinstance(execution, dict):
            raise ValueError("execution result must be a dictionary")

        status = execution.get("status")
        request = execution.get("request")

        if status == "blocked":
            return {
                "status": "blocked",
                "execution_performed": False,
                "reason": execution.get("reason", "execution_blocked"),
                "request": request,
            }

        if status != "completed":
            raise ValueError("execution result must have status completed or blocked")

        normalized_result = self._response_normalizer.normalize(
            execution.get("result"),
            model_name,
        )
        return {
            "status": "completed",
            "execution_performed": True,
            "request": request,
            "result": normalized_result,
        }

    def failure(
        self,
        model_name: str,
        request: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        if not isinstance(model_name, str) or not model_name.strip():
            raise ValueError("model_name must be a non-empty string")
        return {
            "status": "failed",
            "execution_performed": True,
            "reason": "provider_execution_failed",
            "model": model_name,
            "request": request,
        }
