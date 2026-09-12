from backend.app.reality.retrieval_provider_capabilities import RetrievalProviderCapabilities
from backend.app.reality.retrieval_provider_request import RetrievalProviderRequest


class RetrievalProviderCapabilityEvaluator:
    """Evaluate provider capability fit independently of provider selection."""

    @staticmethod
    def evaluate(
        capabilities: RetrievalProviderCapabilities,
        request: RetrievalProviderRequest,
    ) -> bool:
        if not isinstance(capabilities, RetrievalProviderCapabilities):
            raise ValueError("capabilities must be a RetrievalProviderCapabilities")
        if not isinstance(request, RetrievalProviderRequest):
            raise ValueError("request must be a RetrievalProviderRequest")
        return capabilities.supports(request)


__all__ = ["RetrievalProviderCapabilityEvaluator"]
