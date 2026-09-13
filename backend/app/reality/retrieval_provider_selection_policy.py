from typing import Protocol, runtime_checkable

from backend.app.reality.retrieval_provider_availability_evaluation import RetrievalProviderAvailabilityEvaluationResult
from backend.app.reality.retrieval_provider_capability_evaluation import RetrievalProviderCapabilityEvaluationResult
from backend.app.reality.retrieval_provider_health_evaluation import RetrievalProviderHealthEvaluationResult
from backend.app.reality.retrieval_provider_selection_policy_result import RetrievalProviderSelectionPolicyResult


@runtime_checkable
class RetrievalProviderSelectionPolicy(Protocol):
    """Policy contract for deciding whether all provider-selection gates pass."""

    def evaluate(
        self,
        source_type: str,
        availability: RetrievalProviderAvailabilityEvaluationResult,
        health: RetrievalProviderHealthEvaluationResult,
        capability: RetrievalProviderCapabilityEvaluationResult | None,
    ) -> RetrievalProviderSelectionPolicyResult:
        """Return a stable result for the combined provider-selection policy decision."""
        ...


class DefaultRetrievalProviderSelectionPolicy:
    """Default fail-closed policy for provider-selection gate outcomes."""

    def evaluate(
        self,
        source_type: str,
        availability: RetrievalProviderAvailabilityEvaluationResult,
        health: RetrievalProviderHealthEvaluationResult,
        capability: RetrievalProviderCapabilityEvaluationResult | None,
    ) -> RetrievalProviderSelectionPolicyResult:
        if not isinstance(source_type, str) or not source_type.strip():
            raise ValueError("source_type must be a nonempty string")
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

        if not availability.supported:
            return RetrievalProviderSelectionPolicyResult.rejected_result(
                source_type,
                availability.reason or "retrieval_provider_unavailable",
            )
        if not health.supported:
            return RetrievalProviderSelectionPolicyResult.rejected_result(
                source_type,
                health.reason or "retrieval_provider_unhealthy",
            )
        if capability is not None and not capability.supported:
            return RetrievalProviderSelectionPolicyResult.rejected_result(
                source_type,
                capability.reason or "retrieval_provider_capability_mismatch",
            )

        return RetrievalProviderSelectionPolicyResult.allowed_result(source_type)


__all__ = [
    "DefaultRetrievalProviderSelectionPolicy",
    "RetrievalProviderSelectionPolicy",
]
