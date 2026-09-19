from typing import Any


class RetrievalResultContract:
    """Create validated, provider-neutral result envelopes for reality retrieval."""

    @staticmethod
    def completed(
        request: dict[str, Any],
        provider: str | None,
        sources: list[dict[str, Any]],
        content: str | None,
    ) -> dict[str, Any]:
        return _build_result(
            status="completed",
            request=request,
            provider=provider,
            sources=sources,
            content=content,
            retrieval_executed=True,
        )

    @staticmethod
    def failed(
        request: dict[str, Any],
        provider: str | None,
        reason: str = "retrieval_provider_failed",
    ) -> dict[str, Any]:
        return _build_result(
            status="failed",
            request=request,
            provider=provider,
            sources=[],
            content=None,
            reason=reason,
            retrieval_executed=True,
        )

    @staticmethod
    def blocked(
        request: dict[str, Any],
        provider: str | None,
        reason: str = "retrieval_provider_unavailable",
    ) -> dict[str, Any]:
        return _build_result(
            status="blocked",
            request=request,
            provider=provider,
            sources=[],
            content=None,
            reason=reason,
            retrieval_executed=False,
        )

    @staticmethod
    def validate(result: object) -> dict[str, Any]:
        """Validate an existing retrieval-result envelope without changing it."""
        if not isinstance(result, dict):
            raise ValueError("retrieval result must be a dictionary")

        required = {
            "status", "provider", "request", "sources",
            "content", "retrieval_executed",
        }
        if not required.issubset(result):
            raise ValueError("retrieval result is missing required fields")

        return _build_result(
            status=result["status"],
            request=result["request"],
            provider=result["provider"],
            sources=result["sources"],
            content=result["content"],
            retrieval_executed=result["retrieval_executed"],
            reason=result.get("reason"),
        )
    @staticmethod
    def not_required(request: dict[str, Any]) -> dict[str, Any]:
        """Build the canonical result used when retrieval is not required."""
        return _build_result(
            status="not_required",
            request=request,
            provider=None,
            sources=[],
            content=None,
            retrieval_executed=False,
        )


def _build_result(
    *,
    status: str,
    request: dict[str, Any],
    provider: str | None,
    sources: list[dict[str, Any]],
    content: str | None,
    retrieval_executed: bool,
    reason: str | None = None,
) -> dict[str, Any]:
    """Validate and build the canonical provider-neutral retrieval result."""
    if status not in {"completed", "failed", "blocked", "not_required"}:
        raise ValueError("status must be completed, failed, blocked, or not_required")

    if not isinstance(request, dict):
        raise ValueError("request must be a dictionary")

    if provider is not None:
        if not isinstance(provider, str) or not provider.strip():
            raise ValueError("provider must be a nonempty string when provided")
        provider = provider.strip()

    if not isinstance(sources, list):
        raise ValueError("sources must be a list")
    if any(not isinstance(source, dict) for source in sources):
        raise ValueError("each source must be a dictionary")

    if content is not None and not isinstance(content, str):
        raise ValueError("content must be a string or None")

    if status in {"failed", "blocked"}:
        if sources:
            raise ValueError("non-completed results must not contain sources")
        if content is not None:
            raise ValueError("non-completed results must not contain content")
        if reason is None or not isinstance(reason, str) or not reason.strip():
            raise ValueError("failed or blocked results require a nonempty reason")
        reason = reason.strip()
    elif status == "not_required":
        if provider is not None:
            raise ValueError("not_required results must not contain a provider")
        if sources:
            raise ValueError("not_required results must not contain sources")
        if content is not None:
            raise ValueError("not_required results must not contain content")
        if reason is not None:
            raise ValueError("not_required results must not contain a reason")
    elif reason is not None:
        raise ValueError("completed results must not contain a reason")

    expected_execution = status in {"completed", "failed"}
    if retrieval_executed is not expected_execution:
        raise ValueError("retrieval_executed is inconsistent with result status")

    result = {
        "status": status,
        "provider": provider,
        "request": dict(request),
        "sources": [dict(source) for source in sources],
        "content": content,
        "retrieval_executed": retrieval_executed,
    }
    if reason is not None:
        result["reason"] = reason
    return result


__all__ = ["RetrievalResultContract"]
