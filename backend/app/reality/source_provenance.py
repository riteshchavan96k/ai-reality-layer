from dataclasses import dataclass
from typing import Any


@dataclass(frozen=True)
class SourceProvenance:
    """Stable identity record for an evidence source."""

    source_id: str
    source_ref: str
    uri: str
    title: str | None = None
    identity_method: str = "sha256_uri"

    def __post_init__(self) -> None:
        for value, name in (
            (self.source_id, "source_id"),
            (self.source_ref, "source_ref"),
            (self.uri, "uri"),
        ):
            if not isinstance(value, str) or not value.strip():
                raise ValueError(f"{name} must be a non-empty string")
        if self.title is not None and not isinstance(self.title, str):
            raise ValueError("title must be a string or None")
        if self.identity_method != "sha256_uri":
            raise ValueError("identity_method must be sha256_uri")

    def to_dict(self) -> dict[str, Any]:
        return {
            "source_id": self.source_id,
            "source_ref": self.source_ref,
            "uri": self.uri,
            "title": self.title,
            "identity_method": self.identity_method,
        }


@dataclass(frozen=True)
class SourceProvenanceResult:
    """Canonical result of assigning stable identities to evidence sources."""

    status: str
    sources: tuple[SourceProvenance, ...] = ()
    source_count: int = 0
    provenance_executed: bool = True
    reason: str | None = None

    def __post_init__(self) -> None:
        if self.status not in {"usable", "empty", "unavailable"}:
            raise ValueError("status must be usable, empty, or unavailable")
        if not isinstance(self.sources, tuple) or any(not isinstance(source, SourceProvenance) for source in self.sources):
            raise ValueError("sources must be a tuple of SourceProvenance values")
        if not isinstance(self.source_count, int) or self.source_count < 0:
            raise ValueError("source_count must be a non-negative integer")
        if self.source_count != len(self.sources):
            raise ValueError("source_count must match the number of sources")
        if not isinstance(self.provenance_executed, bool):
            raise ValueError("provenance_executed must be a boolean")
        if self.status == "usable" and not self.sources:
            raise ValueError("usable source provenance requires at least one source")
        if self.status == "empty" and self.sources:
            raise ValueError("empty source provenance cannot contain sources")
        if self.status == "unavailable" and self.sources:
            raise ValueError("unavailable source provenance cannot contain sources")
        if self.status == "unavailable" and (not isinstance(self.reason, str) or not self.reason.strip()):
            raise ValueError("unavailable source provenance requires a reason")
        if self.status != "unavailable" and self.reason is not None:
            raise ValueError("usable or empty source provenance cannot contain a reason")

    @classmethod
    def usable_result(cls, sources: tuple[SourceProvenance, ...]) -> "SourceProvenanceResult":
        return cls("usable", sources=sources, source_count=len(sources))

    @classmethod
    def empty_result(cls) -> "SourceProvenanceResult":
        return cls("empty")

    @classmethod
    def unavailable_result(cls, reason: str) -> "SourceProvenanceResult":
        return cls("unavailable", reason=reason)

    def to_dict(self) -> dict[str, Any]:
        return {
            "status": self.status,
            "sources": [source.to_dict() for source in self.sources],
            "source_count": self.source_count,
            "provenance_executed": self.provenance_executed,
            "reason": self.reason,
        }


__all__ = ["SourceProvenance", "SourceProvenanceResult"]
