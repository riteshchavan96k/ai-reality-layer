from dataclasses import dataclass
from typing import Any


@dataclass(frozen=True)
class SourceFreshnessAssessment:
    """Canonical freshness assessment for one observed source."""

    source_id: str
    status: str
    observed_at: str
    age_seconds: float | None = None
    max_age_seconds: float | None = None
    assessment_method: str = "observation_age"
    reason: str | None = None

    def __post_init__(self) -> None:
        if not isinstance(self.source_id, str) or not self.source_id.strip():
            raise ValueError("source_id must be a non-empty string")
        if self.status not in {"fresh", "stale", "unknown"}:
            raise ValueError("status must be fresh, stale, or unknown")
        if not isinstance(self.observed_at, str) or not self.observed_at.strip():
            raise ValueError("observed_at must be a non-empty string")
        if self.age_seconds is not None and (not isinstance(self.age_seconds, (int, float)) or self.age_seconds < 0):
            raise ValueError("age_seconds must be a non-negative number or None")
        if self.max_age_seconds is not None and (not isinstance(self.max_age_seconds, (int, float)) or self.max_age_seconds <= 0):
            raise ValueError("max_age_seconds must be a positive number or None")
        if self.status in {"fresh", "stale"} and (self.age_seconds is None or self.max_age_seconds is None):
            raise ValueError("fresh or stale assessment requires age_seconds and max_age_seconds")
        if self.status == "unknown" and self.reason is None:
            raise ValueError("unknown assessment requires a reason")
        if self.status != "unknown" and self.reason is not None:
            raise ValueError("fresh or stale assessment cannot contain a reason")
        if self.assessment_method != "observation_age":
            raise ValueError("assessment_method must be observation_age")

    def to_dict(self) -> dict[str, Any]:
        return {
            "source_id": self.source_id,
            "status": self.status,
            "observed_at": self.observed_at,
            "age_seconds": self.age_seconds,
            "max_age_seconds": self.max_age_seconds,
            "assessment_method": self.assessment_method,
            "reason": self.reason,
        }


@dataclass(frozen=True)
class SourceFreshnessResult:
    """Canonical result for source freshness evaluation."""

    status: str
    assessments: tuple[SourceFreshnessAssessment, ...] = ()
    source_count: int = 0
    fresh_count: int = 0
    stale_count: int = 0
    unknown_count: int = 0
    freshness_executed: bool = True
    reason: str | None = None

    def __post_init__(self) -> None:
        if self.status not in {"usable", "empty", "unavailable"}:
            raise ValueError("status must be usable, empty, or unavailable")
        if not isinstance(self.assessments, tuple) or any(not isinstance(item, SourceFreshnessAssessment) for item in self.assessments):
            raise ValueError("assessments must be a tuple of SourceFreshnessAssessment values")
        if self.source_count != len(self.assessments):
            raise ValueError("source_count must match the number of assessments")
        counts = {
            "fresh": sum(item.status == "fresh" for item in self.assessments),
            "stale": sum(item.status == "stale" for item in self.assessments),
            "unknown": sum(item.status == "unknown" for item in self.assessments),
        }
        if (self.fresh_count, self.stale_count, self.unknown_count) != (counts["fresh"], counts["stale"], counts["unknown"]):
            raise ValueError("freshness counts must match assessment states")
        if not isinstance(self.freshness_executed, bool):
            raise ValueError("freshness_executed must be a boolean")
        if self.status == "usable" and not self.assessments:
            raise ValueError("usable freshness result requires assessments")
        if self.status in {"empty", "unavailable"} and self.assessments:
            raise ValueError(f"{self.status} freshness result cannot contain assessments")
        if self.status == "unavailable" and (not isinstance(self.reason, str) or not self.reason.strip()):
            raise ValueError("unavailable freshness result requires a reason")
        if self.status != "unavailable" and self.reason is not None:
            raise ValueError("usable or empty freshness result cannot contain a reason")

    @classmethod
    def usable_result(cls, assessments: tuple[SourceFreshnessAssessment, ...]) -> "SourceFreshnessResult":
        return cls(
            "usable",
            assessments=assessments,
            source_count=len(assessments),
            fresh_count=sum(item.status == "fresh" for item in assessments),
            stale_count=sum(item.status == "stale" for item in assessments),
            unknown_count=sum(item.status == "unknown" for item in assessments),
        )

    @classmethod
    def empty_result(cls) -> "SourceFreshnessResult":
        return cls("empty")

    @classmethod
    def unavailable_result(cls, reason: str) -> "SourceFreshnessResult":
        return cls("unavailable", reason=reason)

    def to_dict(self) -> dict[str, Any]:
        return {
            "status": self.status,
            "assessments": [item.to_dict() for item in self.assessments],
            "source_count": self.source_count,
            "fresh_count": self.fresh_count,
            "stale_count": self.stale_count,
            "unknown_count": self.unknown_count,
            "freshness_executed": self.freshness_executed,
            "reason": self.reason,
        }


__all__ = ["SourceFreshnessAssessment", "SourceFreshnessResult"]
