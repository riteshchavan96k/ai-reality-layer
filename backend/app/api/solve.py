from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, Field, model_validator

from backend.app.orchestrator.result_normalizer import (
    OrchestrationResultNormalizer,
)


SolveStatus = Literal[
    "awaiting_human_approval",
    "retrieval_unavailable",
    "grounding_unavailable",
    "execution_context_unavailable",
    "execution_failed",
    "orchestrated",
]


class SolveRequest(BaseModel):
    """HTTP request contract for orchestration-backed solve requests."""

    model_config = ConfigDict(extra="forbid")

    task: str = Field(min_length=1, max_length=10_000)
    human_approved: bool = False


class SolveResponse(BaseModel):
    """HTTP response contract backed by the canonical orchestration result."""

    model_config = ConfigDict(extra="allow")

    status: SolveStatus
    analysis: dict[str, Any]
    routing: dict[str, Any]
    approval: dict[str, Any]
    trace: list[dict[str, Any]]

    retrieval: dict[str, Any] | None = None
    evidence: dict[str, Any] | None = None
    evidence_quality: dict[str, Any] | None = None
    grounding: dict[str, Any] | None = None
    execution_context: dict[str, Any] | None = None
    execution: dict[str, Any] | None = None
    result: dict[str, Any] | None = None
    evaluation: dict[str, Any] | None = None
    quality_recovery: dict[str, Any] | None = None
    outcome: dict[str, Any] | None = None

    @model_validator(mode="before")
    @classmethod
    def validate_canonical_orchestration_result(cls, value: object) -> object:
        """Require the HTTP response to satisfy the Step 172 public contract."""
        return OrchestrationResultNormalizer.normalize(value).to_dict()


__all__ = ["SolveRequest", "SolveResponse", "SolveStatus"]
