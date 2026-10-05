from dataclasses import dataclass
from typing import Any, Mapping

from backend.app.reality.retrieval_input_bounds import validate_retrieved_evidence_bounds


@dataclass(frozen=True)
class RetrievalProviderResponse:
    """Validated provider output before retrieval-result normalization."""

    status: str = "completed"
    sources: tuple[dict[str, Any], ...] = ()
    content: str | None = None
    provider: str | None = None
    reason: str | None = None

    def __post_init__(self) -> None:
        if self.status not in {"completed", "failed", "blocked", "provider_unavailable"}:
            raise ValueError("status must be a supported retrieval provider status")
        if not isinstance(self.sources, tuple):
            raise ValueError("sources must be a tuple")
        if any(not isinstance(source, dict) for source in self.sources):
            raise ValueError("each source must be a dictionary")
        if self.content is not None and not isinstance(self.content, str):
            raise ValueError("content must be a string or None")
        if self.provider is not None:
            if not isinstance(self.provider, str) or not self.provider.strip():
                raise ValueError("provider must be a nonempty string when provided")
            object.__setattr__(self, "provider", self.provider.strip())
        if self.reason is not None:
            if not isinstance(self.reason, str) or not self.reason.strip():
                raise ValueError("reason must be a nonempty string when provided")
            object.__setattr__(self, "reason", self.reason.strip())
        if self.status == "completed":
            bounds_reason = validate_retrieved_evidence_bounds(
                self.sources, self.content,
            )
            if bounds_reason is not None:
                raise ValueError(f"retrieved evidence bounds: {bounds_reason}")
        if self.status != "completed" and self.sources:
            raise ValueError("non-completed responses must not contain sources")
        if self.status != "completed" and self.content is not None:
            raise ValueError("non-completed responses must not contain content")

    @classmethod
    def from_mapping(cls, response: Mapping[str, Any]) -> "RetrievalProviderResponse":
        if not isinstance(response, Mapping):
            raise ValueError("response must be a mapping")

        status = response.get("status", "completed")
        sources = response.get("sources", [])
        if not isinstance(sources, list):
            raise ValueError("sources must be a list")

        return cls(
            status=status,
            sources=tuple(sources),
            content=response.get("content"),
            provider=response.get("provider"),
            reason=response.get("reason"),
        )

    def to_dict(self) -> dict[str, Any]:
        return {
            "status": self.status,
            "sources": [dict(source) for source in self.sources],
            "content": self.content,
            "provider": self.provider,
            "reason": self.reason,
        }


__all__ = ["RetrievalProviderResponse"]
