from backend.app.reality.retrieval_provider_capabilities import RetrievalProviderCapabilities
from backend.app.reality.retrieval_provider_capability_evaluation import RetrievalProviderCapabilityEvaluationResult
from backend.app.reality.retrieval_provider_request import RetrievalProviderRequest


class RetrievalProviderCapabilityEvaluator:
    """Evaluate provider capability fit and return a stable evaluation result."""

    @staticmethod
    def evaluate(capabilities: RetrievalProviderCapabilities, request: RetrievalProviderRequest) -> RetrievalProviderCapabilityEvaluationResult:
        if not isinstance(capabilities, RetrievalProviderCapabilities):
            raise ValueError("capabilities must be a RetrievalProviderCapabilities")
        if not isinstance(request, RetrievalProviderRequest):
            raise ValueError("request must be a RetrievalProviderRequest")
        if capabilities.supports(request):
            return RetrievalProviderCapabilityEvaluationResult.supported_result(request)
        return RetrievalProviderCapabilityEvaluationResult.unsupported_result(request)


__all__ = ["RetrievalProviderCapabilityEvaluator"]
