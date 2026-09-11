from typing import Any, Mapping, Protocol


class RetrievalProviderSelector(Protocol):
    """Select the retrieval provider that should handle a structured request."""

    def select(self, request: Mapping[str, Any]) -> Any:
        """Return the provider selected for the request."""
        ...


class RegistryRetrievalProviderSelector:
    """Deterministically select a provider from an explicit source-type registry."""

    def __init__(self, providers: Mapping[str, Any], default_provider: Any) -> None:
        self._providers = dict(providers)
        self._default_provider = default_provider

    def select(self, request: Mapping[str, Any]) -> Any:
        source_type = request.get("source_type")
        return self._providers.get(source_type, self._default_provider)


__all__ = ["RegistryRetrievalProviderSelector", "RetrievalProviderSelector"]
