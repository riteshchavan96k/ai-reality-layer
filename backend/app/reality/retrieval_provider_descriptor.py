from dataclasses import dataclass
from typing import Any

from backend.app.reality.retrieval_provider import RetrievalProvider
from backend.app.reality.retrieval_provider_capabilities import RetrievalProviderCapabilities


@dataclass(frozen=True)
class RetrievalProviderDescriptor:
    """Stable metadata describing a retrieval provider without executing it."""

    name: str
    capabilities: RetrievalProviderCapabilities
    provider: RetrievalProvider

    def __post_init__(self) -> None:
        if not isinstance(self.name, str) or not self.name.strip():
            raise ValueError("provider name must be a nonempty string")
        object.__setattr__(self, "name", self.name.strip())

    def supports(self, request: Any) -> bool:
        """Return whether the descriptor's capabilities support the request."""
        return self.capabilities.supports(request)

    def to_dict(self) -> dict[str, Any]:
        return {
            "name": self.name,
            "capabilities": self.capabilities.to_dict(),
        }


__all__ = ["RetrievalProviderDescriptor"]
