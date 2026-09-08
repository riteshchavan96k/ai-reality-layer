from typing import Any, Callable

from backend.app.models.provider_invocation import ProviderInvocationContract
from backend.app.models.registry import get_model_adapter


class ProviderInvocationExecutor:
    """Execute a validated invocation through the model adapter boundary."""

    def __init__(
        self,
        adapter_resolver: Callable[[str], Any] | None = None,
        invocation_contract: ProviderInvocationContract | None = None,
    ):
        self._adapter_resolver = adapter_resolver or get_model_adapter
        self._invocation_contract = invocation_contract or ProviderInvocationContract()

    def execute(
        self,
        provider_name: str,
        model_name: str,
        task: str,
        context: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        invocation = self._invocation_contract.build(
            provider_name=provider_name,
            model_name=model_name,
            task=task,
            context=context,
        )
        request = invocation["request"]

        adapter = self._adapter_resolver(model_name)
        if adapter is None:
            return {
                "status": "blocked",
                "execution_performed": False,
                "reason": "model_adapter_unavailable",
                "request": request,
            }

        result = adapter.generate(task, context=context)
        return {
            "status": "completed",
            "execution_performed": True,
            "request": request,
            "result": result,
        }
