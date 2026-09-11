from typing import Any


class RetrievalResultContract:
    """Create stable, provider-neutral result envelopes for reality retrieval."""

    @staticmethod
    def completed(
        request: dict[str, Any],
        provider: str | None,
        sources: list[dict[str, Any]],
        content: str | None,
    ) -> dict[str, Any]:
        return {
            "status": "completed",
            "provider": provider,
            "request": dict(request),
            "sources": list(sources),
            "content": content,
            "retrieval_executed": True,
        }

    @staticmethod
    def failed(
        request: dict[str, Any],
        provider: str | None,
        reason: str = "retrieval_provider_failed",
    ) -> dict[str, Any]:
        return {
            "status": "failed",
            "provider": provider,
            "request": dict(request),
            "sources": [],
            "content": None,
            "reason": reason,
            "retrieval_executed": True,
        }

    @staticmethod
    def blocked(
        request: dict[str, Any],
        provider: str | None,
        reason: str = "retrieval_provider_unavailable",
    ) -> dict[str, Any]:
        return {
            "status": "blocked",
            "provider": provider,
            "request": dict(request),
            "sources": [],
            "content": None,
            "reason": reason,
            "retrieval_executed": False,
        }
