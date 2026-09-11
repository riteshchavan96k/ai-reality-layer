from typing import Any, Protocol


class RetrievalProvider(Protocol):
    """Provider contract for retrieving reality information from a source."""

    def retrieve(self, request: dict[str, Any]) -> dict[str, Any]:
        """Retrieve information for a structured retrieval request."""
        ...


__all__ = ["RetrievalProvider"]
