from dataclasses import dataclass, field
from math import isfinite
from typing import Any, Mapping


def _validate_evaluation_fields(
    score: object,
    status: object,
    details: object,
) -> None:
    if (
        not isinstance(score, (int, float))
        or isinstance(score, bool)
        or not isfinite(float(score))
        or not 0.0 <= float(score) <= 1.0
    ):
        raise ValueError("score must be a finite number between 0 and 1")
    if status not in {"pass", "review"}:
        raise ValueError("status must be 'pass' or 'review'")
    if not isinstance(details, Mapping):
        raise ValueError("details must be a mapping")

    checks = details.get("checks")
    if checks is not None and (
        not isinstance(checks, Mapping)
        or any(
            not isinstance(name, str)
            or not name.strip()
            or not isinstance(value, bool)
            for name, value in checks.items()
        )
    ):
        raise ValueError(
            "checks must map non-empty check names to booleans"
        )

    for name in ("passed_checks", "total_checks"):
        value = details.get(name)
        if value is not None and (
            not isinstance(value, int)
            or isinstance(value, bool)
            or value < 0
        ):
            raise ValueError(f"{name} must be a non-negative integer")

    passed_checks = details.get("passed_checks")
    total_checks = details.get("total_checks")
    if (
        passed_checks is not None
        and total_checks is not None
        and passed_checks > total_checks
    ):
        raise ValueError("passed_checks cannot exceed total_checks")

    structural_score = details.get("structural_score")
    if structural_score is not None and (
        not isinstance(structural_score, (int, float))
        or isinstance(structural_score, bool)
        or not isfinite(float(structural_score))
        or not 0.0 <= float(structural_score) <= 1.0
    ):
        raise ValueError(
            "structural_score must be a finite number between 0 and 1"
        )

    relevance = details.get("relevance")
    if relevance is not None and not isinstance(relevance, Mapping):
        raise ValueError("relevance must be a mapping when present")

    task = details.get("task")
    if task is not None and (
        not isinstance(task, str) or not task.strip()
    ):
        raise ValueError("task must be a non-empty string when present")

    limitation = details.get("limitation")
    if limitation is not None and (
        not isinstance(limitation, str) or not limitation.strip()
    ):
        raise ValueError(
            "limitation must be a non-empty string when present"
        )


@dataclass(frozen=True)
class ResponseEvaluationResult:
    """Canonical contract for one response-evaluation outcome."""

    score: int | float
    status: str
    details: dict[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        _validate_evaluation_fields(
            self.score,
            self.status,
            self.details,
        )
        object.__setattr__(self, "details", dict(self.details))

    @classmethod
    def validate(
        cls,
        raw: "ResponseEvaluationResult | Mapping[str, Any]",
    ) -> "ResponseEvaluationResult":
        if isinstance(raw, cls):
            return raw
        if not isinstance(raw, Mapping):
            raise TypeError(
                "response evaluation result must be a mapping or ResponseEvaluationResult"
            )

        missing = sorted({"score", "status"} - set(raw))
        if missing:
            raise ValueError(
                f"response evaluation result missing fields: {', '.join(missing)}"
            )

        details = {
            key: value
            for key, value in raw.items()
            if key not in {"score", "status"}
        }

        return cls(
            score=raw["score"],
            status=raw["status"],
            details=dict(details),
        )

    def to_dict(self) -> dict[str, Any]:
        return {
            "score": self.score,
            "status": self.status,
            **dict(self.details),
        }


__all__ = ["ResponseEvaluationResult"]
