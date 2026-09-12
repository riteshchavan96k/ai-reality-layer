from dataclasses import dataclass
from typing import Any

from backend.app.reality.retrieval_provider_request import RetrievalProviderRequest


@dataclass(frozen=True)
class RetrievalProviderCapabilityEvaluationResult:
    """Stable result of evaluating provider capability fit for a request."""

    status: str
    source_type: str
    temporal_scope: str
    supported: bool
    reason: str | None = None

    @classmethod
    def supported_result(cls, request: RetrievalProviderRequest) -> "RetrievalProviderCapabilityEvaluationResult":
        return cls("supported", request.source_type, request.temporal_scope, True)

    @classmethod
    def unsupported_result(cls, request: RetrievalProviderRequest, reason: str = "retrieval_provider_capability_mismatch") -> "RetrievalProviderCapabilityEvaluationResult":
        return cls("unsupported", request.source_type, request.temporal_scope, False, reason)

    @property
    def evaluation_executed(self) -> bool:
        return True

    def to_dict(self) -> dict[str, Any]:
        return {"status": self.status, "source_type": self.source_type, "temporal_scope": self.temporal_scope, "supported": self.supported, "reason": self.reason, "evaluation_executed": self.evaluation_executed}


__all__ = ["RetrievalProviderCapabilityEvaluationResult"]
