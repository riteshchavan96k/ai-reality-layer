from dataclasses import dataclass
from typing import Any


@dataclass(frozen=True)
class GroundingExecutionContext:
    """Canonical, provenance-preserving context handed from grounding into execution."""

    task: str
    grounding_status: str
    content: str | None
    sources: list[dict[str, Any]]
    source_count: int
    execution_allowed: bool = True
    context_prepared: bool = True

    def __post_init__(self) -> None:
        if not isinstance(self.task, str) or not self.task.strip():
            raise ValueError("task must be a non-empty string")
        if self.grounding_status not in {"ready", "not_available"}:
            raise ValueError("grounding_status must be ready or not_available")
        if self.content is not None and not isinstance(self.content, str):
            raise ValueError("content must be a string or None")
        if not isinstance(self.sources, list) or not all(isinstance(source, dict) for source in self.sources):
            raise ValueError("sources must be a list of dictionaries")
        if not isinstance(self.source_count, int) or self.source_count < 0:
            raise ValueError("source_count must be a non-negative integer")
        if self.source_count != len(self.sources):
            raise ValueError("source_count must match sources")
        if not isinstance(self.execution_allowed, bool):
            raise ValueError("execution_allowed must be a boolean")
        if not isinstance(self.context_prepared, bool):
            raise ValueError("context_prepared must be a boolean")
        if self.grounding_status == "not_available":
            if self.content is not None:
                raise ValueError("not_available execution context cannot contain content")
            if self.sources:
                raise ValueError("not_available execution context cannot contain sources")
            if self.source_count != 0:
                raise ValueError("not_available execution context must have source_count=0")

    @classmethod
    def from_grounding(
        cls,
        grounding: dict[str, Any],
        execution_allowed: bool = True,
    ) -> "GroundingExecutionContext":
        """Build an execution context from an already-normalized grounding mapping."""
        sources = grounding.get("sources", [])
        if not isinstance(sources, list):
            raise ValueError("grounding sources must be a list")
        if not all(isinstance(source, dict) for source in sources):
            raise ValueError("grounding sources must be dictionaries")
        return cls(
            task=grounding["task"],
            grounding_status=grounding["status"],
            content=grounding.get("content"),
            sources=[dict(source) for source in sources],
            source_count=grounding["source_count"],
            execution_allowed=execution_allowed,
        )

    @classmethod
    def ready_result(
        cls,
        task: str,
        content: str | None,
        sources: list[dict[str, Any]],
    ) -> "GroundingExecutionContext":
        return cls(
            task=task,
            grounding_status="ready",
            content=content,
            sources=list(sources),
            source_count=len(sources),
        )

    @classmethod
    def not_available_result(cls, task: str) -> "GroundingExecutionContext":
        return cls(
            task=task,
            grounding_status="not_available",
            content=None,
            sources=[],
            source_count=0,
        )

    def to_dict(self) -> dict[str, Any]:
        return {
            "task": self.task,
            "grounding_status": self.grounding_status,
            "content": self.content,
            "sources": [dict(source) for source in self.sources],
            "source_count": self.source_count,
            "execution_allowed": self.execution_allowed,
            "context_prepared": self.context_prepared,
        }


__all__ = ["GroundingExecutionContext"]
