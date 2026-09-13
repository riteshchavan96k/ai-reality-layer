from dataclasses import dataclass
from typing import Any

from backend.app.reality.retrieval_provider import RetrievalProvider
from backend.app.reality.retrieval_provider_selection_decision import RetrievalProviderSelectionDecision
from backend.app.reality.retrieval_provider_selection_decision_normalizer import (
    RetrievalProviderSelectionDecisionNormalizer,
)


@dataclass(frozen=True)
class RetrievalProviderSelectionResult:
    """Stable result contract for retrieval-provider resolution."""

    status: str
    source_type: str
    provider: RetrievalProvider | None = None
    reason: str | None = None
    decision: RetrievalProviderSelectionDecision | None = None

    def __post_init__(self) -> None:
        if self.status not in {"selected", "unavailable"}:
            raise ValueError("status must be selected or unavailable")
        if not isinstance(self.source_type, str) or not self.source_type.strip():
            raise ValueError("source_type must be a nonempty string")
        if self.status == "selected" and self.provider is None:
            raise ValueError("selected status requires a provider")
        if self.status == "unavailable" and self.provider is not None:
            raise ValueError("unavailable status cannot contain a provider")
        if self.reason is not None and (not isinstance(self.reason, str) or not self.reason.strip()):
            raise ValueError("reason must be a nonempty string when provided")
        if self.decision is not None:
            normalized = RetrievalProviderSelectionDecisionNormalizer.normalize(self.decision)
            if normalized.status == "selected" and self.status != "selected":
                raise ValueError("selected decision requires selected result status")
            if normalized.status == "rejected" and self.status != "unavailable":
                raise ValueError("rejected decision requires unavailable result status")
            object.__setattr__(self, "decision", normalized)

    @classmethod
    def selected(
        cls,
        source_type: str,
        provider: RetrievalProvider,
        decision: RetrievalProviderSelectionDecision | Any | None = None,
    ) -> "RetrievalProviderSelectionResult":
        return cls(status="selected", source_type=source_type, provider=provider, decision=decision)

    @classmethod
    def unavailable(
        cls,
        source_type: str,
        reason: str = "retrieval_provider_unavailable",
        decision: RetrievalProviderSelectionDecision | Any | None = None,
    ) -> "RetrievalProviderSelectionResult":
        return cls(status="unavailable", source_type=source_type, reason=reason, decision=decision)

    @property
    def selection_executed(self) -> bool:
        return self.status == "selected"


__all__ = ["RetrievalProviderSelectionResult"]
