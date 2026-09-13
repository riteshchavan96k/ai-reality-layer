from backend.app.reality.retrieval_provider_health_contract import RetrievalProviderHealth
from backend.app.reality.retrieval_provider_health_evaluation import RetrievalProviderHealthEvaluationResult


class RetrievalProviderHealthEvaluator:
    """Evaluate provider health and return a stable evaluation result."""

    @staticmethod
    def evaluate(health: RetrievalProviderHealth) -> RetrievalProviderHealthEvaluationResult:
        if not isinstance(health, RetrievalProviderHealth):
            raise ValueError("health must be a RetrievalProviderHealth")
        if health.status == "healthy":
            return RetrievalProviderHealthEvaluationResult.healthy(health)
        if health.status == "unhealthy":
            return RetrievalProviderHealthEvaluationResult.unhealthy(health)
        return RetrievalProviderHealthEvaluationResult.unknown(health)


__all__ = ["RetrievalProviderHealthEvaluator"]
