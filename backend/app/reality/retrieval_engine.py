from typing import Any, Protocol


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
    """Execute a retrieval contract through a pluggable provider."""

    def __init__(self, provider: RetrievalProvider | None = None) -> None:
        self.provider = provider or UnconfiguredRetrievalProvider()

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
            }

        if not isinstance(request, dict):
            raise ValueError("retrieval contract request must be a dictionary")

        result = self.provider.retrieve(request)
        if not isinstance(result, dict):
            raise ValueError("retrieval provider must return a dictionary")

        return {
            "status": result.get("status", "completed"),
            "provider": result.get("provider"),
            "request": request,
            "sources": list(result.get("sources", [])),
            "content": result.get("content"),
        }
