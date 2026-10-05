from dataclasses import dataclass
from typing import Any

from backend.app.reality.freshness_policy import (
    is_nonnegative_finite_number,
    is_positive_finite_number,
)


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
        if self.age_seconds is not None and not is_nonnegative_finite_number(self.age_seconds):
            raise ValueError("age_seconds must be a non-negative number or None")
        if self.max_age_seconds is not None and not is_positive_finite_number(self.max_age_seconds):
            raise ValueError("max_age_seconds must be a positive number or None")
        if self.status in {"fresh", "stale"} and (self.age_seconds is None or self.max_age_seconds is None):
            raise ValueError("fresh or stale assessment requires age_seconds and max_age_seconds")
        if self.status == "unknown" and (not isinstance(self.reason, str) or not self.reason.strip()):
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
        if not isinstance(self.source_count, int) or self.source_count < 0:
            raise ValueError("source_count must be a non-negative integer")
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

    @classmethod
    def validate(cls, raw_result: object) -> "SourceFreshnessResult":
        """Validate or normalize a canonical source-freshness result."""
        if isinstance(raw_result, cls):
            return raw_result
        if not isinstance(raw_result, dict):
            raise ValueError("source freshness result must be a mapping or SourceFreshnessResult")
        required = {"status", "assessments", "source_count", "fresh_count", "stale_count", "unknown_count", "freshness_executed", "reason"}
        missing = sorted(required - set(raw_result))
        if missing:
            raise ValueError(f"missing required fields: {', '.join(missing)}")
        raw_assessments = raw_result["assessments"]
        if not isinstance(raw_assessments, (list, tuple)):
            raise ValueError("assessments must be a list or tuple")
        assessments: list[SourceFreshnessAssessment] = []
        for raw_assessment in raw_assessments:
            if isinstance(raw_assessment, SourceFreshnessAssessment):
                assessments.append(raw_assessment)
                continue
            if not isinstance(raw_assessment, dict):
                raise ValueError("each freshness assessment must be a mapping or SourceFreshnessAssessment")
            assessment_required = {"source_id", "status", "observed_at", "age_seconds", "max_age_seconds", "assessment_method", "reason"}
            assessment_missing = sorted(assessment_required - set(raw_assessment))
            if assessment_missing:
                raise ValueError(f"freshness assessment is missing required fields: {', '.join(assessment_missing)}")
            assessments.append(SourceFreshnessAssessment(
                source_id=raw_assessment["source_id"],
                status=raw_assessment["status"],
                observed_at=raw_assessment["observed_at"],
                age_seconds=raw_assessment["age_seconds"],
                max_age_seconds=raw_assessment["max_age_seconds"],
                assessment_method=raw_assessment["assessment_method"],
                reason=raw_assessment["reason"],
            ))
        return cls(
            status=raw_result["status"],
            assessments=tuple(assessments),
            source_count=raw_result["source_count"],
            fresh_count=raw_result["fresh_count"],
            stale_count=raw_result["stale_count"],
            unknown_count=raw_result["unknown_count"],
            freshness_executed=raw_result["freshness_executed"],
            reason=raw_result["reason"],
        )

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
