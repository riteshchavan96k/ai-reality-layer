from typing import Protocol, runtime_checkable

from backend.app.reality.retrieval_provider_availability_evaluation import RetrievalProviderAvailabilityEvaluationResult
from backend.app.reality.retrieval_provider_capability_evaluation import RetrievalProviderCapabilityEvaluationResult
from backend.app.reality.retrieval_provider_health_evaluation import RetrievalProviderHealthEvaluationResult


@runtime_checkable
class RetrievalProviderSelectionPolicy(Protocol):
    """Policy contract for deciding whether all provider-selection gates pass."""

    def allows(
        self,
        availability: RetrievalProviderAvailabilityEvaluationResult,
        health: RetrievalProviderHealthEvaluationResult,
        capability: RetrievalProviderCapabilityEvaluationResult | None,
    ) -> bool:
        """Return whether the provider is eligible after selection gates."""
        ...


class DefaultRetrievalProviderSelectionPolicy:
    """Default fail-closed policy for provider-selection gate outcomes."""

    def allows(
        self,
        availability: RetrievalProviderAvailabilityEvaluationResult,
        health: RetrievalProviderHealthEvaluationResult,
        capability: RetrievalProviderCapabilityEvaluationResult | None,
    ) -> bool:
        if not isinstance(availability, RetrievalProviderAvailabilityEvaluationResult):
            raise ValueError("availability must be a RetrievalProviderAvailabilityEvaluationResult")
        if not isinstance(health, RetrievalProviderHealthEvaluationResult):
            raise ValueError("health must be a RetrievalProviderHealthEvaluationResult")
        if capability is not None and not isinstance(
            capability, RetrievalProviderCapabilityEvaluationResult
        ):
            raise ValueError(
                "capability must be a RetrievalProviderCapabilityEvaluationResult or None"
            )

        return availability.supported and health.supported and (
            capability is None or capability.supported
        )


__all__ = [
    "DefaultRetrievalProviderSelectionPolicy",
    "RetrievalProviderSelectionPolicy",
]
