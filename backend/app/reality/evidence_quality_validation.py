from dataclasses import dataclass
from typing import Any


@dataclass(frozen=True)
class EvidenceQualityValidationResult:
    """Stable result contract for structural and provenance quality validation."""

    status: str
    usable: bool
    source_count: int
    has_content: bool
    provenance_complete: bool
    issues: list[str]
    validation_executed: bool = True

    def __post_init__(self) -> None:
        if self.status not in {"usable", "insufficient", "not_required"}:
            raise ValueError("status must be usable, insufficient, or not_required")
        if not isinstance(self.usable, bool):
            raise ValueError("usable must be a boolean")
        if not isinstance(self.source_count, int) or self.source_count < 0:
            raise ValueError("source_count must be a nonnegative integer")
        if not isinstance(self.has_content, bool):
            raise ValueError("has_content must be a boolean")
        if not isinstance(self.provenance_complete, bool):
            raise ValueError("provenance_complete must be a boolean")
        if not isinstance(self.issues, list) or not all(isinstance(issue, str) and issue.strip() for issue in self.issues):
            raise ValueError("issues must be a list of nonempty strings")
        if not isinstance(self.validation_executed, bool):
            raise ValueError("validation_executed must be a boolean")
        if self.status == "usable" and not self.validation_executed:
            raise ValueError(
                "usable evidence quality requires validation_executed to be True"
            )
        if self.status == "usable" and not self.usable:
            raise ValueError("usable status requires usable=True")
        if self.status != "usable" and self.usable:
            raise ValueError("non-usable status requires usable=False")
        if self.status == "usable" and self.source_count == 0:
            raise ValueError("usable evidence quality requires at least one source")
        if self.status == "usable" and not self.has_content:
            raise ValueError("usable evidence quality requires has_content=True")
        if self.status == "usable" and not self.provenance_complete:
            raise ValueError(
                "usable evidence quality requires provenance_complete=True"
            )
        if self.status == "usable" and self.issues:
            raise ValueError("usable evidence quality cannot contain validation issues")
        if self.status == "not_required" and self.issues:
            raise ValueError("not_required status cannot contain validation issues")

    @classmethod
    def usable_result(cls, source_count: int, has_content: bool, provenance_complete: bool) -> "EvidenceQualityValidationResult":
        return cls(status="usable", usable=True, source_count=source_count, has_content=has_content, provenance_complete=provenance_complete, issues=[])

    @classmethod
    def insufficient_result(cls, source_count: int, has_content: bool, provenance_complete: bool, issues: list[str]) -> "EvidenceQualityValidationResult":
        return cls(status="insufficient", usable=False, source_count=source_count, has_content=has_content, provenance_complete=provenance_complete, issues=list(issues))

    @classmethod
    def not_required_result(cls, source_count: int, has_content: bool, provenance_complete: bool) -> "EvidenceQualityValidationResult":
        return cls(status="not_required", usable=False, source_count=source_count, has_content=has_content, provenance_complete=provenance_complete, issues=[])

    def to_dict(self) -> dict[str, Any]:
        return {"status": self.status, "usable": self.usable, "source_count": self.source_count, "has_content": self.has_content, "provenance_complete": self.provenance_complete, "issues": list(self.issues), "validation_executed": self.validation_executed}


__all__ = ["EvidenceQualityValidationResult"]
