from typing import Any

from backend.app.reality.retrieval_provider import RetrievalProvider
from backend.app.reality.retrieval_provider_request import RetrievalProviderRequest
from backend.app.reality.retrieval_provider_response_normalizer import (
    RetrievalProviderResponseNormalizer,
)
from backend.app.reality.retrieval_result import RetrievalResultContract
from backend.app.reality.retrieval_result_normalizer import RetrievalResultNormalizer


class RetrievalProviderExecutor:
    """Execute a retrieval provider through a stable provider-neutral boundary."""

    def execute(
        self,
        provider: RetrievalProvider,
        request: RetrievalProviderRequest,
    ) -> dict[str, Any]:
        """Execute a provider with typed request/response contracts."""
        provider_name = _provider_identity(provider)
        request_dict = request.to_dict()

        try:
            raw_result = provider.retrieve(request)
        except Exception:
            return RetrievalResultContract.failed(request_dict, provider_name)

        try:
            response = RetrievalProviderResponseNormalizer.normalize(raw_result)
            return RetrievalResultNormalizer.normalize(
                request_dict,
                response,
                fallback_provider=provider_name,
            )
        except (TypeError, ValueError):
            return RetrievalResultContract.failed(request_dict, provider_name)


__all__ = ["RetrievalProviderExecutor"]


def _provider_identity(provider: RetrievalProvider) -> str | None:
    """Return a stable provider identity from the provider implementation."""
    for attribute in ("provider_name", "name"):
        value = getattr(provider, attribute, None)
        if isinstance(value, str) and value.strip():
            return value
    return None
