from typing import Any, Mapping, Protocol

from backend.app.reality.retrieval_provider import RetrievalProvider
from backend.app.reality.retrieval_provider_availability_evaluator import RetrievalProviderAvailabilityEvaluator
from backend.app.reality.retrieval_provider_capability_evaluator import RetrievalProviderCapabilityEvaluator
from backend.app.reality.retrieval_provider_capability_evaluation import RetrievalProviderCapabilityEvaluationResult
from backend.app.reality.retrieval_provider_health_evaluator import RetrievalProviderHealthEvaluator
from backend.app.reality.retrieval_provider_registry import RetrievalProviderRegistry
from backend.app.reality.retrieval_provider_request import RetrievalProviderRequest
from backend.app.reality.retrieval_provider_selection import RetrievalProviderSelectionResult
from backend.app.reality.retrieval_provider_selection_policy import (
    DefaultRetrievalProviderSelectionPolicy,
    RetrievalProviderSelectionPolicy,
)


class RetrievalProviderSelector(Protocol):
    """Select the retrieval provider that should handle a structured request."""

    def select(self, request: Mapping[str, Any]) -> RetrievalProviderSelectionResult:
        """Return a stable provider-selection result for the request."""
        ...


class RegistryRetrievalProviderSelector:
    """Select a provider through availability, health, registry, and capabilities."""

    def __init__(
        self,
        registry: RetrievalProviderRegistry,
        capability_evaluator: RetrievalProviderCapabilityEvaluator | None = None,
        availability_evaluator: RetrievalProviderAvailabilityEvaluator | None = None,
        health_evaluator: RetrievalProviderHealthEvaluator | None = None,
        selection_policy: RetrievalProviderSelectionPolicy | None = None,
    ) -> None:
        self._registry = registry
        self._capability_evaluator = capability_evaluator or RetrievalProviderCapabilityEvaluator()
        self._availability_evaluator = availability_evaluator or RetrievalProviderAvailabilityEvaluator()
        self._health_evaluator = health_evaluator or RetrievalProviderHealthEvaluator()
        self._selection_policy = selection_policy or DefaultRetrievalProviderSelectionPolicy()

    def select(self, request: Mapping[str, Any]) -> RetrievalProviderSelectionResult:
        source_type = request.get("source_type")
        provider = self._registry.get(source_type)
        if provider is None:
            return RetrievalProviderSelectionResult.unavailable(source_type)

        availability = self._registry.get_availability(source_type)
        availability_evaluation = self._availability_evaluator.evaluate(availability)
        if not availability_evaluation.supported:
            return RetrievalProviderSelectionResult.unavailable(
                source_type,
                reason=availability_evaluation.reason or "retrieval_provider_unavailable",
            )

        health = self._registry.get_health(source_type)
        health_evaluation = self._health_evaluator.evaluate(health)
        if not health_evaluation.supported:
            return RetrievalProviderSelectionResult.unavailable(
                source_type,
                reason=health_evaluation.reason or "retrieval_provider_unhealthy",
            )

        capability_evaluation: RetrievalProviderCapabilityEvaluationResult | None = None
        descriptor = self._registry.get_descriptor(source_type)
        if descriptor is not None:
            typed_request = RetrievalProviderRequest.from_mapping(request)
            capability_evaluation = self._capability_evaluator.evaluate(
                descriptor.capabilities,
                typed_request,
            )
            if not capability_evaluation.supported:
                return RetrievalProviderSelectionResult.unavailable(
                    source_type,
                    reason=capability_evaluation.reason or "retrieval_provider_capability_mismatch",
                )

        policy_result = self._selection_policy.evaluate(
            source_type,
            availability_evaluation,
            health_evaluation,
            capability_evaluation,
        )
        if not policy_result.allowed:
            return RetrievalProviderSelectionResult.unavailable(
                source_type,
                reason=policy_result.reason or "retrieval_provider_selection_policy_rejected",
            )

        return RetrievalProviderSelectionResult.selected(source_type, provider)


__all__ = ["RegistryRetrievalProviderSelector", "RetrievalProviderSelector"]
