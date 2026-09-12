from dataclasses import dataclass
from typing import Any

from backend.app.reality.retrieval_provider import RetrievalProvider
from backend.app.reality.retrieval_provider_capabilities import RetrievalProviderCapabilities
from backend.app.reality.retrieval_provider_identity import RetrievalProviderIdentity


@dataclass(frozen=True)
class RetrievalProviderDescriptor:
    """Stable metadata describing a retrieval provider without executing it."""

    identity: RetrievalProviderIdentity
    capabilities: RetrievalProviderCapabilities
    provider: RetrievalProvider

    def supports(self, request: Any) -> bool:
        """Return whether the descriptor's capabilities support the request."""
        return self.capabilities.supports(request)

    def to_dict(self) -> dict[str, Any]:
        return {
            "identity": self.identity.to_dict(),
            "capabilities": self.capabilities.to_dict(),
        }


__all__ = ["RetrievalProviderDescriptor"]
