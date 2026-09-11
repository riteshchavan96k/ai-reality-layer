from dataclasses import dataclass
from typing import Any


@dataclass(frozen=True)
class RetrievalProviderSelectionResult:
    """Stable result contract for retrieval-provider resolution."""

    status: str
    source_type: str
    provider: Any = None
    reason: str | None = None

    @classmethod
    def selected(cls, source_type: str, provider: Any) -> "RetrievalProviderSelectionResult":
        return cls(status="selected", source_type=source_type, provider=provider)

    @classmethod
    def unavailable(cls, source_type: str, reason: str = "retrieval_provider_unavailable") -> "RetrievalProviderSelectionResult":
        return cls(status="unavailable", source_type=source_type, reason=reason)

    @property
    def selection_executed(self) -> bool:
        return self.status == "selected"


__all__ = ["RetrievalProviderSelectionResult"]
