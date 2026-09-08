from dataclasses import dataclass
from typing import Any


@dataclass(frozen=True)
class ProviderInvocationRequest:
    """Validated, provider-neutral request envelope for future execution."""

    provider_name: str
    model_name: str
    task: str
    context: dict[str, Any] | None = None

    def __post_init__(self):
        if not isinstance(self.provider_name, str) or not self.provider_name.strip():
            raise ValueError("provider_name must be a non-empty string")
        if not isinstance(self.model_name, str) or not self.model_name.strip():
            raise ValueError("model_name must be a non-empty string")
        if not isinstance(self.task, str) or not self.task.strip():
            raise ValueError("task must be a non-empty string")
        if self.context is not None and not isinstance(self.context, dict):
            raise ValueError("context must be a dictionary when provided")

    def to_dict(self) -> dict[str, Any]:
        return {
            "provider_name": self.provider_name,
            "model_name": self.model_name,
            "task": self.task,
            "context": self.context,
        }


class ProviderInvocationContract:
    """Build a deterministic invocation request without performing execution."""

    def build(
        self,
        provider_name: str,
        model_name: str,
        task: str,
        context: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        request = ProviderInvocationRequest(
            provider_name=provider_name,
            model_name=model_name,
            task=task,
            context=context,
        )
        return {
            "status": "ready",
            "execution_performed": False,
            "request": request.to_dict(),
        }
