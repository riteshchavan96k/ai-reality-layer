from dataclasses import dataclass

from backend.app.reality.retrieval_provider import RetrievalProvider
from backend.app.reality.retrieval_provider_selection_decision import RetrievalProviderSelectionDecision


@dataclass(frozen=True)
class RetrievalProviderSelectionResult:
    """Stable result contract for retrieval-provider resolution."""

    status: str
    source_type: str
    provider: RetrievalProvider | None = None
    reason: str | None = None
    decision: RetrievalProviderSelectionDecision | None = None

    @classmethod
    def selected(
        cls,
        source_type: str,
        provider: RetrievalProvider,
        decision: RetrievalProviderSelectionDecision | None = None,
    ) -> "RetrievalProviderSelectionResult":
        return cls(status="selected", source_type=source_type, provider=provider, decision=decision)

    @classmethod
    def unavailable(
        cls,
        source_type: str,
        reason: str = "retrieval_provider_unavailable",
        decision: RetrievalProviderSelectionDecision | None = None,
    ) -> "RetrievalProviderSelectionResult":
        return cls(status="unavailable", source_type=source_type, reason=reason, decision=decision)

    @property
    def selection_executed(self) -> bool:
        return self.status == "selected"


__all__ = ["RetrievalProviderSelectionResult"]
