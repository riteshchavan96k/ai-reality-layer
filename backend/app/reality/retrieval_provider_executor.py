from typing import Any

from backend.app.reality.retrieval_provider import RetrievalProvider
from backend.app.reality.retrieval_provider_request import RetrievalProviderRequest
from backend.app.reality.retrieval_result import RetrievalResultContract


class RetrievalProviderExecutor:
    """Execute a retrieval provider through a stable provider-neutral boundary."""

    def execute(
        self,
        provider: RetrievalProvider,
        request: RetrievalProviderRequest,
    ) -> dict[str, Any]:
        """Execute a provider with a validated request and normalize its outcome."""
        provider_name = getattr(provider, "name", None)
        request_dict = request.to_dict()

        try:
            result = provider.retrieve(request)
        except Exception:
            return RetrievalResultContract.failed(request_dict, provider_name)

        if not isinstance(result, dict):
            return RetrievalResultContract.failed(request_dict, provider_name)

        result_status = result.get("status", "completed")
        result_provider = result.get("provider", provider_name)

        if result_status in {"provider_unavailable", "blocked"}:
            return RetrievalResultContract.blocked(
                request_dict,
                result_provider,
                "retrieval_provider_unavailable",
            )

        if result_status == "failed":
            return RetrievalResultContract.failed(
                request_dict,
                result_provider,
                "retrieval_provider_failed",
            )

        sources = result.get("sources", [])
        content = result.get("content")
        if not isinstance(sources, list):
            return RetrievalResultContract.failed(request_dict, result_provider)
        if content is not None and not isinstance(content, str):
            return RetrievalResultContract.failed(request_dict, result_provider)

        return RetrievalResultContract.completed(
            request_dict,
            result_provider,
            sources,
            content,
        )


__all__ = ["RetrievalProviderExecutor"]
