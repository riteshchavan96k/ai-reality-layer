from dataclasses import dataclass
from typing import Any


@dataclass(frozen=True)
class GroundingContext:
    """Stable contract for provenance-preserving context supplied to execution."""

    status: str
    task: str
    content: str | None
    sources: list[dict[str, Any]]
    source_count: int
    grounding_executed: bool = True

    def __post_init__(self) -> None:
        if self.status not in {"ready", "not_available"}:
            raise ValueError("status must be ready or not_available")
        if not isinstance(self.task, str) or not self.task.strip():
            raise ValueError("task must be a non-empty string")
        if self.content is not None and not isinstance(self.content, str):
            raise ValueError("content must be a string or None")
        if not isinstance(self.sources, list) or not all(isinstance(source, dict) for source in self.sources):
            raise ValueError("sources must be a list of dictionaries")
        if not isinstance(self.source_count, int) or self.source_count < 0:
            raise ValueError("source_count must be a non-negative integer")
        if self.source_count != len(self.sources):
            raise ValueError("source_count must match sources")
        if not isinstance(self.grounding_executed, bool):
            raise ValueError("grounding_executed must be a boolean")
        if self.status == "not_available":
            if self.content is not None:
                raise ValueError("not_available grounding context cannot contain content")
            if self.sources:
                raise ValueError("not_available grounding context cannot contain sources")
            if self.source_count != 0:
                raise ValueError("not_available grounding context must have source_count=0")

    @classmethod
    def ready_result(
        cls,
        task: str,
        content: str | None,
        sources: list[dict[str, Any]],
    ) -> "GroundingContext":
        return cls(
            status="ready",
            task=task,
            content=content,
            sources=list(sources),
            source_count=len(sources),
        )

    @classmethod
    def not_available_result(cls, task: str) -> "GroundingContext":
        return cls(
            status="not_available",
            task=task,
            content=None,
            sources=[],
            source_count=0,
        )

    def to_dict(self) -> dict[str, Any]:
        return {
            "status": self.status,
            "task": self.task,
            "content": self.content,
            "sources": [dict(source) for source in self.sources],
            "source_count": self.source_count,
            "grounding_executed": self.grounding_executed,
        }


__all__ = ["GroundingContext"]
