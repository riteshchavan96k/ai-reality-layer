from typing import Any, Mapping, Protocol

from backend.app.reality.retrieval_provider import RetrievalProvider
from backend.app.reality.retrieval_provider_registry import RetrievalProviderRegistry
from backend.app.reality.retrieval_provider_selection import RetrievalProviderSelectionResult


class RetrievalProviderSelector(Protocol):
    """Select the retrieval provider that should handle a structured request."""

    def select(self, request: Mapping[str, Any]) -> RetrievalProviderSelectionResult:
        """Return a stable provider-selection result for the request."""
        ...


class RegistryRetrievalProviderSelector:
    """Select a provider through the dedicated retrieval provider registry."""

    def __init__(self, registry: RetrievalProviderRegistry) -> None:
        self._registry = registry

    def select(self, request: Mapping[str, Any]) -> RetrievalProviderSelectionResult:
        source_type = request.get("source_type")
        provider = self._registry.get(source_type)
        if provider is None:
            return RetrievalProviderSelectionResult.unavailable(
                source_type,
            )
        return RetrievalProviderSelectionResult.selected(source_type, provider)


__all__ = ["RegistryRetrievalProviderSelector", "RetrievalProviderSelector"]
