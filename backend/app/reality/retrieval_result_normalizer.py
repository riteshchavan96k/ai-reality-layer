from typing import Any

from backend.app.reality.retrieval_provider_response import RetrievalProviderResponse
from backend.app.reality.retrieval_result import RetrievalResultContract


class RetrievalResultNormalizer:
    """Normalize a provider response into the stable retrieval-result envelope."""

    @staticmethod
    def normalize(
        request: dict[str, Any],
        response: RetrievalProviderResponse,
        fallback_provider: str | None = None,
    ) -> dict[str, Any]:
        if not isinstance(response, RetrievalProviderResponse):
            raise ValueError("retrieval result normalization requires a provider response")

        provider = response.provider or fallback_provider

        if response.status in {"provider_unavailable", "blocked"}:
            return RetrievalResultContract.blocked(
                request,
                provider,
                response.reason or "retrieval_provider_unavailable",
            )

        if response.status == "failed":
            return RetrievalResultContract.failed(
                request,
                provider,
                response.reason or "retrieval_provider_failed",
            )

        if response.status == "completed":
            return RetrievalResultContract.completed(
                request,
                provider,
                list(response.sources),
                response.content,
            )

        raise ValueError("unsupported retrieval provider response status")


__all__ = ["RetrievalResultNormalizer"]
