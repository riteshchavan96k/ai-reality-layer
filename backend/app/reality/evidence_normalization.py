from dataclasses import dataclass
from typing import Any


@dataclass(frozen=True)
class EvidenceNormalizationResult:
    """Stable result contract for normalized retrieval evidence."""

    status: str
    sources: list[dict[str, Any]]
    content: str | None
    source_count: int
    has_content: bool
    normalization_executed: bool = True

    def __post_init__(self) -> None:
        if self.status not in {"completed", "not_required", "invalid_evidence", "unknown"}:
            raise ValueError("status must be a supported evidence status")
        if not isinstance(self.sources, list):
            raise ValueError("sources must be a list")
        if not all(isinstance(source, dict) for source in self.sources):
            raise ValueError("each evidence source must be a dictionary")
        if self.content is not None and not isinstance(self.content, str):
            raise ValueError("content must be a string or None")
        if not isinstance(self.source_count, int) or self.source_count < 0:
            raise ValueError("source_count must be a nonnegative integer")
        if self.source_count != len(self.sources):
            raise ValueError("source_count must match the number of sources")
        if not isinstance(self.has_content, bool):
            raise ValueError("has_content must be a boolean")
        expected_has_content = bool(self.content and self.content.strip())
        if self.has_content != expected_has_content:
            raise ValueError("has_content must match content presence")
        if not isinstance(self.normalization_executed, bool):
            raise ValueError("normalization_executed must be a boolean")

    @classmethod
    def validate(cls, result: object) -> "EvidenceNormalizationResult":
        """Validate an existing evidence-normalization contract."""
        if isinstance(result, cls):
            return result

        if not isinstance(result, dict):
            raise ValueError("evidence normalization result must be a dictionary")

        required = {
            "status",
            "sources",
            "content",
            "source_count",
            "has_content",
            "normalization_executed",
        }
        if not required.issubset(result):
            raise ValueError("evidence normalization result is missing required fields")

        return cls(
            status=result["status"],
            sources=result["sources"],
            content=result["content"],
            source_count=result["source_count"],
            has_content=result["has_content"],
            normalization_executed=result["normalization_executed"],
        )

    @classmethod
    def from_mapping(cls, evidence: dict[str, Any]) -> "EvidenceNormalizationResult":
        if not isinstance(evidence, dict):
            raise ValueError("evidence must be a dictionary")

        values = {
            "status": evidence.get("status", "unknown"),
            "sources": evidence.get("sources", []),
            "content": evidence.get("content"),
            "source_count": evidence.get("source_count", len(evidence.get("sources", []))),
            "has_content": evidence.get(
                "has_content", bool(evidence.get("content") and str(evidence.get("content")).strip())
            ),
            "normalization_executed": evidence.get("normalization_executed", True),
        }
        return cls.validate(values)

    def to_dict(self) -> dict[str, Any]:
        return {
            "status": self.status,
            "sources": [dict(source) for source in self.sources],
            "content": self.content,
            "source_count": self.source_count,
            "has_content": self.has_content,
            "normalization_executed": self.normalization_executed,
        }


__all__ = ["EvidenceNormalizationResult"]
