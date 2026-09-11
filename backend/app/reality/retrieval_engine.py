from typing import Any, Protocol

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
                "retrieval_executed": False,
            }

        if not isinstance(request, dict):
            raise ValueError("retrieval contract request must be a dictionary")

        provider_name = getattr(self.provider, "name", None)

        try:
            result = self.provider.retrieve(request)
        except Exception:
            return RetrievalResultContract.failed(request, provider_name)

        if not isinstance(result, dict):
            return RetrievalResultContract.failed(request, provider_name)

        result_status = result.get("status", "completed")
        result_provider = result.get("provider", provider_name)

        if result_status in {"provider_unavailable", "blocked"}:
            return RetrievalResultContract.blocked(
                request,
                result_provider,
                "retrieval_provider_unavailable",
            )

        if result_status == "failed":
            return RetrievalResultContract.failed(
                request,
                result_provider,
                "retrieval_provider_failed",
            )

        sources = result.get("sources", [])
        content = result.get("content")
        if not isinstance(sources, list):
            return RetrievalResultContract.failed(request, result_provider)
        if content is not None and not isinstance(content, str):
            return RetrievalResultContract.failed(request, result_provider)

        return RetrievalResultContract.completed(
            request,
            result_provider,
            sources,
            content,
        )
