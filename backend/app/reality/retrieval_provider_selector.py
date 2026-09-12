from typing import Any, Mapping, Protocol

from backend.app.reality.retrieval_provider import RetrievalProvider
from backend.app.reality.retrieval_provider_capability_evaluator import RetrievalProviderCapabilityEvaluator
from backend.app.reality.retrieval_provider_registry import RetrievalProviderRegistry
from backend.app.reality.retrieval_provider_request import RetrievalProviderRequest
from backend.app.reality.retrieval_provider_selection import RetrievalProviderSelectionResult


class RetrievalProviderSelector(Protocol):
    """Select the retrieval provider that should handle a structured request."""

    def select(self, request: Mapping[str, Any]) -> RetrievalProviderSelectionResult:
        """Return a stable provider-selection result for the request."""
        ...


class RegistryRetrievalProviderSelector:
    """Select a provider through availability, registry lookup, and capabilities."""

    def __init__(self, registry: RetrievalProviderRegistry, capability_evaluator: RetrievalProviderCapabilityEvaluator | None = None) -> None:
        self._registry = registry
        self._capability_evaluator = capability_evaluator or RetrievalProviderCapabilityEvaluator()

    def select(self, request: Mapping[str, Any]) -> RetrievalProviderSelectionResult:
        source_type = request.get("source_type")
        provider = self._registry.get(source_type)
        if provider is None:
            return RetrievalProviderSelectionResult.unavailable(source_type)

        availability = self._registry.get_availability(source_type)
        if not availability.is_available:
            return RetrievalProviderSelectionResult.unavailable(
                source_type,
                reason=availability.reason or "retrieval_provider_unavailable",
            )

        descriptor = self._registry.get_descriptor(source_type)
        if descriptor is not None:
            typed_request = RetrievalProviderRequest.from_mapping(request)
            evaluation = self._capability_evaluator.evaluate(descriptor.capabilities, typed_request)
            if not evaluation.supported:
                return RetrievalProviderSelectionResult.unavailable(
                    source_type,
                    reason=evaluation.reason or "retrieval_provider_capability_mismatch",
                )
        return RetrievalProviderSelectionResult.selected(source_type, provider)


__all__ = ["RegistryRetrievalProviderSelector", "RetrievalProviderSelector"]
