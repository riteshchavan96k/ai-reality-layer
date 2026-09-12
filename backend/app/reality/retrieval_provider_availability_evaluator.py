from backend.app.reality.retrieval_provider_availability import RetrievalProviderAvailability


class RetrievalProviderAvailabilityEvaluator:
    """Evaluate whether a retrieval provider is currently eligible for selection."""

    @staticmethod
    def evaluate(availability: RetrievalProviderAvailability) -> bool:
        if not isinstance(availability, RetrievalProviderAvailability):
            raise ValueError("availability must be a RetrievalProviderAvailability")
        return availability.is_available


__all__ = ["RetrievalProviderAvailabilityEvaluator"]
