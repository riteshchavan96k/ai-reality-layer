from collections.abc import Mapping

from backend.app.reality.retrieval_provider_response import RetrievalProviderResponse


class RetrievalProviderResponseNormalizer:
    """Normalize typed or legacy provider output into the canonical response contract."""

    @staticmethod
    def normalize(raw_response: object) -> RetrievalProviderResponse:
        if isinstance(raw_response, RetrievalProviderResponse):
            return raw_response

        if isinstance(raw_response, Mapping):
            return RetrievalProviderResponse.from_mapping(raw_response)

        raise ValueError("retrieval provider response must be a response contract or mapping")


__all__ = ["RetrievalProviderResponseNormalizer"]
