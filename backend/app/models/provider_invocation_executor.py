from typing import Any, Callable

from backend.app.models.provider_invocation import ProviderInvocationContract
from backend.app.models.provider_execution_result import ProviderExecutionResultContract
from backend.app.models.registry import get_model_adapter


class ProviderInvocationExecutor:
    """Execute a validated invocation through the model adapter boundary."""

    def __init__(
        self,
        adapter_resolver: Callable[[str], Any] | None = None,
        invocation_contract: ProviderInvocationContract | None = None,
        result_contract: ProviderExecutionResultContract | None = None,
    ):
        self._adapter_resolver = adapter_resolver or get_model_adapter
        self._invocation_contract = invocation_contract or ProviderInvocationContract()
        self._result_contract = result_contract or ProviderExecutionResultContract()

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
            return self._result_contract.blocked(
                provider_name=provider_name,
                model_name=model_name,
                request=request,
            )

        try:
            result = adapter.generate(task, context=context)
            completed = self._result_contract.completed(result, model_name)
        except Exception:
            return self._result_contract.failed(
                provider_name=provider_name,
                model_name=model_name,
                request=request,
            )

        return {
            **completed,
            "request": request,
        }
