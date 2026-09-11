from typing import Any, Mapping


class RetrievalProviderRegistry:
    """Own the mapping between retrieval source types and provider implementations."""

    def __init__(
        self,
        providers: Mapping[str, Any] | None = None,
        default_provider: Any = None,
    ) -> None:
        self._providers = dict(providers or {})
        self._default_provider = default_provider

    def register(self, source_type: str, provider: Any) -> None:
        """Register or replace the provider responsible for a source type."""
        normalized_source_type = self._normalize_source_type(source_type)
        self._providers[normalized_source_type] = provider

    def get(self, source_type: str) -> Any:
        """Return the provider registered for a source type, or the default provider."""
        normalized_source_type = self._normalize_source_type(source_type)
        return self._providers.get(normalized_source_type, self._default_provider)

    def default_provider(self) -> Any:
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
