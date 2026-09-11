from typing import Any, Protocol

from backend.app.reality.retrieval_provider_executor import RetrievalProviderExecutor
from backend.app.reality.retrieval_result import RetrievalResultContract


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
    """Execute retrieval through a provider and return a stable result boundary."""

    def __init__(
        self,
        provider: RetrievalProvider | None = None,
        provider_executor: RetrievalProviderExecutor | None = None,
    ) -> None:
        self.provider = provider or UnconfiguredRetrievalProvider()
        self.provider_executor = provider_executor or RetrievalProviderExecutor()

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

        return self.provider_executor.execute(self.provider, request)


__all__ = ["RealityRetrievalEngine", "RetrievalProvider", "UnconfiguredRetrievalProvider"]
