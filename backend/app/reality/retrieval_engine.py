from typing import Any, Protocol

from backend.app.reality.retrieval_provider_executor import RetrievalProviderExecutor
from backend.app.reality.retrieval_provider_selector import (
    RegistryRetrievalProviderSelector,
    RetrievalProviderSelector,
)


class RetrievalProvider(Protocol):
    """Provider interface for future external reality-information retrieval."""

    def retrieve(self, request: dict[str, Any]) -> dict[str, Any]:
        """Retrieve information for a structured retrieval request."""
        ...


class UnconfiguredRetrievalProvider:
    """Explicit provider used until a real external retrieval provider is configured."""

    def retrieve(self, request: dict[str, Any]) -> dict[str, Any]:
        return {
            "status": "provider_unavailable",
            "provider": None,
            "request": dict(request),
            "sources": [],
            "content": None,
        }


class RealityRetrievalEngine:
    """Select and execute retrieval providers through stable provider-neutral boundaries."""

    def __init__(
        self,
        provider: RetrievalProvider | None = None,
        provider_executor: RetrievalProviderExecutor | None = None,
        provider_selector: RetrievalProviderSelector | None = None,
    ) -> None:
        self.provider_executor = provider_executor or RetrievalProviderExecutor()

        if provider_selector is not None:
            self.provider_selector = provider_selector
        else:
            selected_provider = provider or UnconfiguredRetrievalProvider()
            self.provider_selector = RegistryRetrievalProviderSelector(
                providers={},
                default_provider=selected_provider,
            )

    def retrieve(self, contract: dict[str, Any]) -> dict[str, Any]:
        if not isinstance(contract, dict):
            raise ValueError("contract must be a dictionary")

        status = contract.get("status")
        request = contract.get("request")

        if status == "not_required":
            return {
                "status": "not_required",
                "provider": None,
                "request": request,
                "sources": [],
                "content": None,
                "retrieval_executed": False,
            }

        if not isinstance(request, dict):
            raise ValueError("retrieval contract request must be a dictionary")

        provider = self.provider_selector.select(request)
        return self.provider_executor.execute(provider, request)


__all__ = ["RealityRetrievalEngine", "RetrievalProvider", "UnconfiguredRetrievalProvider"]
