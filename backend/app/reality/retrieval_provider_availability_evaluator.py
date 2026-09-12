from backend.app.reality.retrieval_provider_availability import RetrievalProviderAvailability
from backend.app.reality.retrieval_provider_availability_evaluation import (
    RetrievalProviderAvailabilityEvaluationResult,
)


class RetrievalProviderAvailabilityEvaluator:
    """Evaluate whether a retrieval provider is currently eligible for selection."""

    @staticmethod
    def evaluate(
        availability: RetrievalProviderAvailability,
    ) -> RetrievalProviderAvailabilityEvaluationResult:
        if not isinstance(availability, RetrievalProviderAvailability):
            raise ValueError("availability must be a RetrievalProviderAvailability")
        return RetrievalProviderAvailabilityEvaluationResult.from_availability(availability)


__all__ = ["RetrievalProviderAvailabilityEvaluator"]
