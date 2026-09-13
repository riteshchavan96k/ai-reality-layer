from backend.app.reality.retrieval_provider_health_contract import RetrievalProviderHealth


class RetrievalProviderHealthEvaluator:
    """Evaluate whether a retrieval provider is healthy for selection."""

    @staticmethod
    def evaluate(health: RetrievalProviderHealth) -> bool:
        if not isinstance(health, RetrievalProviderHealth):
            raise ValueError("health must be a RetrievalProviderHealth")
        return health.is_healthy


__all__ = ["RetrievalProviderHealthEvaluator"]
