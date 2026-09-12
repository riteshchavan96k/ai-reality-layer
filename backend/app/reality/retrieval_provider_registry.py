from typing import Mapping

from backend.app.reality.retrieval_provider import RetrievalProvider
from backend.app.reality.retrieval_provider_descriptor import RetrievalProviderDescriptor


class RetrievalProviderRegistry:
    """Own source-type provider mappings and optional provider descriptors."""

    def __init__(
        self,
        providers: Mapping[str, RetrievalProvider] | None = None,
        default_provider: RetrievalProvider | None = None,
    ) -> None:
        self._providers = dict(providers or {})
        self._descriptors: dict[str, RetrievalProviderDescriptor] = {}
        self._default_provider = default_provider

    def register(self, source_type: str, provider: RetrievalProvider) -> None:
        """Register or replace the provider responsible for a source type."""
        normalized_source_type = self._normalize_source_type(source_type)
        self._providers[normalized_source_type] = provider
        self._descriptors.pop(normalized_source_type, None)

    def register_descriptor(
        self,
        source_type: str,
        descriptor: RetrievalProviderDescriptor,
    ) -> None:
        """Register a provider together with its declared capabilities."""
        normalized_source_type = self._normalize_source_type(source_type)
        if not isinstance(descriptor, RetrievalProviderDescriptor):
            raise ValueError("descriptor must be a RetrievalProviderDescriptor")
        self._providers[normalized_source_type] = descriptor.provider
        self._descriptors[normalized_source_type] = descriptor

    def get(self, source_type: str) -> RetrievalProvider | None:
        """Return the provider registered for a source type, or the default provider."""
        normalized_source_type = self._normalize_source_type(source_type)
        return self._providers.get(normalized_source_type, self._default_provider)

    def get_descriptor(self, source_type: str) -> RetrievalProviderDescriptor | None:
        """Return capability metadata for a source type when explicitly registered."""
        normalized_source_type = self._normalize_source_type(source_type)
        return self._descriptors.get(normalized_source_type)

    def default_provider(self) -> RetrievalProvider | None:
        """Return the explicit fallback provider."""
        return self._default_provider

    @staticmethod
    def _normalize_source_type(source_type: str) -> str:
        if not isinstance(source_type, str):
            raise ValueError("source_type must be a string")
        normalized = source_type.strip()
        if not normalized:
            raise ValueError("source_type must not be empty")
        return normalized


__all__ = ["RetrievalProviderRegistry"]
