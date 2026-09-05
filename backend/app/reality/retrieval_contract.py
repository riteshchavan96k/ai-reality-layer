from dataclasses import dataclass
from typing import Any


@dataclass(frozen=True)
class RetrievalRequest:
    """Structured request contract for future reality-information retrieval."""

    query: str
    source_type: str
    temporal_scope: str = "unspecified"
    required: bool = True

    def __post_init__(self) -> None:
        if not self.query.strip():
            raise ValueError("query must not be empty")
        if not self.source_type.strip():
            raise ValueError("source_type must not be empty")

    def to_dict(self) -> dict[str, Any]:
        return {
            "query": self.query,
            "source_type": self.source_type,
            "temporal_scope": self.temporal_scope,
            "required": self.required,
        }


class RealityRetrievalContract:
    """Build a retrieval request from the Step 36 source plan without performing retrieval."""

    def build(self, task: str, source_plan: dict[str, Any]) -> dict[str, Any]:
        if not task.strip():
            raise ValueError("task must not be empty")

        requires_retrieval = source_plan.get("requires_retrieval", False)
        request = RetrievalRequest(
            query=task,
            source_type=source_plan.get("source_type", "model_knowledge"),
            temporal_scope=source_plan.get("temporal_scope", "unspecified"),
            required=requires_retrieval,
        )

        return {
            "status": "ready" if requires_retrieval else "not_required",
            "request": request.to_dict(),
            "retrieval_executed": False,
        }
