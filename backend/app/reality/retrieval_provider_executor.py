from typing import Any

from backend.app.reality.retrieval_provider import RetrievalProvider
from backend.app.reality.retrieval_provider_request import RetrievalProviderRequest
from backend.app.reality.retrieval_provider_response_normalizer import (
    RetrievalProviderResponseNormalizer,
)
from backend.app.reality.retrieval_result import RetrievalResultContract


class RetrievalProviderExecutor:
    """Execute a retrieval provider through a stable provider-neutral boundary."""

    def execute(
        self,
        provider: RetrievalProvider,
        request: RetrievalProviderRequest,
    ) -> dict[str, Any]:
        """Execute a provider with typed request/response contracts."""
        provider_name = getattr(provider, "name", None)
        request_dict = request.to_dict()

        try:
            raw_result = provider.retrieve(request)
        except Exception:
            return RetrievalResultContract.failed(request_dict, provider_name)

        try:
            result = RetrievalProviderResponseNormalizer.normalize(raw_result)
        except (TypeError, ValueError):
            return RetrievalResultContract.failed(request_dict, provider_name)

        result_provider = result.provider or provider_name

        if result.status in {"provider_unavailable", "blocked"}:
            return RetrievalResultContract.blocked(
                request_dict,
                result_provider,
                result.reason or "retrieval_provider_unavailable",
            )

        if result.status == "failed":
            return RetrievalResultContract.failed(
                request_dict,
                result_provider,
                result.reason or "retrieval_provider_failed",
            )

        return RetrievalResultContract.completed(
            request_dict,
            result_provider,
            list(result.sources),
            result.content,
        )


__all__ = ["RetrievalProviderExecutor"]
