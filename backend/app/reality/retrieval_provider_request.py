from dataclasses import dataclass
from typing import Any, Mapping


@dataclass(frozen=True)
class RetrievalProviderRequest:
    """Provider-facing request contract for reality-information retrieval."""

    query: str
    source_type: str
    temporal_scope: str = "unspecified"
    required: bool = True
    freshness_max_age_seconds: float | None = None

    def __post_init__(self) -> None:
        if not isinstance(self.query, str) or not self.query.strip():
            raise ValueError("query must not be empty")
        if not isinstance(self.source_type, str) or not self.source_type.strip():
            raise ValueError("source_type must not be empty")
        if not isinstance(self.temporal_scope, str) or not self.temporal_scope.strip():
            raise ValueError("temporal_scope must not be empty")
        if not isinstance(self.required, bool):
            raise ValueError("required must be a boolean")
        if self.freshness_max_age_seconds is not None and (not isinstance(self.freshness_max_age_seconds, (int, float)) or isinstance(self.freshness_max_age_seconds, bool) or self.freshness_max_age_seconds <= 0):
            raise ValueError("freshness_max_age_seconds must be a positive number or None")

    @classmethod
    def from_mapping(cls, request: Mapping[str, Any]) -> "RetrievalProviderRequest":
        if not isinstance(request, Mapping):
            raise ValueError("request must be a mapping")
        return cls(
            query=request.get("query", ""),
            source_type=request.get("source_type", ""),
            temporal_scope=request.get("temporal_scope", "unspecified"),
            required=request.get("required", True),
            freshness_max_age_seconds=request.get("freshness_max_age_seconds"),
        )

    def to_dict(self) -> dict[str, Any]:
        return {
            "query": self.query,
            "source_type": self.source_type,
            "temporal_scope": self.temporal_scope,
            "required": self.required,
            **({"freshness_max_age_seconds": self.freshness_max_age_seconds} if self.freshness_max_age_seconds is not None else {}),
        }


__all__ = ["RetrievalProviderRequest"]
