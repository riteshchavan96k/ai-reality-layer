from typing import Any, Mapping, Protocol

from backend.app.reality.retrieval_provider_registry import RetrievalProviderRegistry


class RetrievalProviderSelector(Protocol):
    """Select the retrieval provider that should handle a structured request."""

    def select(self, request: Mapping[str, Any]) -> Any:
        """Return the provider selected for the request."""
        ...


class RegistryRetrievalProviderSelector:
    """Select a provider through the dedicated retrieval provider registry."""

    def __init__(self, registry: RetrievalProviderRegistry) -> None:
        self._registry = registry

    def select(self, request: Mapping[str, Any]) -> Any:
        source_type = request.get("source_type")
        return self._registry.get(source_type)


__all__ = ["RegistryRetrievalProviderSelector", "RetrievalProviderSelector"]
