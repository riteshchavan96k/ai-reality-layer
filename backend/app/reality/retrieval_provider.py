from typing import Protocol, runtime_checkable

from backend.app.reality.retrieval_provider_request import RetrievalProviderRequest


@runtime_checkable
class RetrievalProvider(Protocol):
    """Provider contract for retrieving reality information from a typed request."""

    def retrieve(self, request: RetrievalProviderRequest) -> dict[str, object]:
        """Retrieve information for a validated provider request."""
        ...


__all__ = ["RetrievalProvider"]
