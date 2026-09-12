from dataclasses import dataclass
from typing import Any

from backend.app.reality.retrieval_provider_request import RetrievalProviderRequest


@dataclass(frozen=True)
class RetrievalProviderCapabilities:
    """Declared retrieval capabilities used to reason about provider fit."""

    source_types: tuple[str, ...]
    temporal_scopes: tuple[str, ...] = ("unspecified",)

    def __post_init__(self) -> None:
        source_types = _normalize_values(self.source_types, "source_types")
        temporal_scopes = _normalize_values(self.temporal_scopes, "temporal_scopes")
        object.__setattr__(self, "source_types", source_types)
        object.__setattr__(self, "temporal_scopes", temporal_scopes)

    def supports(self, request: RetrievalProviderRequest) -> bool:
        """Return whether the provider declares support for the request shape."""
        if not isinstance(request, RetrievalProviderRequest):
            raise ValueError("request must be a RetrievalProviderRequest")
        return (
            request.source_type.strip().lower() in self.source_types
            and request.temporal_scope.strip().lower() in self.temporal_scopes
        )

    def to_dict(self) -> dict[str, Any]:
        return {
            "source_types": list(self.source_types),
            "temporal_scopes": list(self.temporal_scopes),
        }


def _normalize_values(values: tuple[str, ...], field_name: str) -> tuple[str, ...]:
    if not isinstance(values, tuple) or not values:
        raise ValueError(f"{field_name} must be a nonempty tuple")
    normalized = []
    for value in values:
        if not isinstance(value, str) or not value.strip():
            raise ValueError(f"{field_name} values must be nonempty strings")
        normalized.append(value.strip().lower())
    return tuple(dict.fromkeys(normalized))


__all__ = ["RetrievalProviderCapabilities"]
