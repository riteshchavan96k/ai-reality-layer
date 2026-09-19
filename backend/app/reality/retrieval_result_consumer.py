from typing import Any

from backend.app.reality.retrieval_result import RetrievalResultContract
from backend.app.reality.retrieval_result_consumption import RetrievalResultConsumption


class RetrievalResultConsumer:
    """Classify retrieval results before downstream evidence normalization."""

    def consume(self, retrieval: dict[str, Any]) -> RetrievalResultConsumption:
        retrieval = RetrievalResultContract.validate(retrieval)
        status = retrieval.get("status")
        if status == "completed":
            sources = retrieval.get("sources", [])
            content = retrieval.get("content")
            if not isinstance(sources, list):
                return RetrievalResultConsumption.rejected_result(
                    status, "invalid_retrieval_sources"
                )
            if content is not None and not isinstance(content, str):
                return RetrievalResultConsumption.rejected_result(
                    status, "invalid_retrieval_content"
                )
            if not sources and not content:
                return RetrievalResultConsumption.rejected_result(
                    status, "empty_retrieval_result"
                )
            return RetrievalResultConsumption.usable_result(status)

        if status in {"failed", "blocked"}:
            return RetrievalResultConsumption.rejected_result(
                status, retrieval.get("reason") or f"retrieval_{status}"
            )

        if status == "not_required":
            return RetrievalResultConsumption.usable_result(status)

        return RetrievalResultConsumption.rejected_result(
            str(status), "unsupported_retrieval_status"
        )


__all__ = ["RetrievalResultConsumer"]
