from collections.abc import Mapping, Sequence
from dataclasses import dataclass, field
from typing import Any

from backend.app.evaluation.response_evaluation_contract import (
    ResponseEvaluationResult,
)
from backend.app.evaluation.response_evaluation_normalizer import (
    ResponseEvaluationResultNormalizer,
)


@dataclass(frozen=True)
class QualityRecoveryBest:
    """Canonical selected candidate carried by a quality-recovery result."""

    model: str
    execution: dict[str, Any]
    evaluation: ResponseEvaluationResult

    def __post_init__(self) -> None:
        if not isinstance(self.model, str) or not self.model.strip():
            raise ValueError("best model must be a non-empty string")
        if not isinstance(self.execution, Mapping):
            raise ValueError("best execution must be a mapping")

        if self.execution.get("status") != "success":
            raise ValueError("best execution must have success status")

        execution_model = self.execution.get("model")
        if (
            not isinstance(execution_model, str)
            or not execution_model.strip()
            or execution_model != self.model
        ):
            raise ValueError(
                "best execution model must match the selected best model"
            )

        if not isinstance(self.execution.get("result"), Mapping):
            raise ValueError("best execution must contain a result mapping")

        evaluation = ResponseEvaluationResultNormalizer.normalize(
            self.evaluation
        )
        object.__setattr__(self, "execution", dict(self.execution))
        object.__setattr__(self, "evaluation", evaluation)

    @classmethod
    def validate(
        cls,
        raw: "QualityRecoveryBest | Mapping[str, Any]",
    ) -> "QualityRecoveryBest":
        if isinstance(raw, cls):
            return raw
        if not isinstance(raw, Mapping):
            raise TypeError(
                "quality recovery best result must be a mapping or QualityRecoveryBest"
            )

        required = {"model", "execution", "evaluation"}
        missing = sorted(required - set(raw))
        if missing:
            raise ValueError(
                f"quality recovery best result missing fields: {', '.join(missing)}"
            )

        return cls(
            model=raw["model"],
            execution=dict(raw["execution"])
            if isinstance(raw["execution"], Mapping)
            else raw["execution"],
            evaluation=ResponseEvaluationResultNormalizer.normalize(
                raw["evaluation"]
            ),
        )

    def to_dict(self) -> dict[str, Any]:
        return {
            "model": self.model,
            "execution": dict(self.execution),
            "evaluation": self.evaluation.to_dict(),
        }


@dataclass(frozen=True)
class QualityRecoveryResult:
    """Canonical envelope for one evaluation-guided recovery outcome."""

    used: bool
    reason: str
    improved: bool
    best: QualityRecoveryBest
    recovery_attempts: int
    candidates_tried: tuple[str, ...]
    details: dict[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        if not isinstance(self.used, bool):
            raise ValueError("used must be a boolean")
        if not isinstance(self.reason, str) or not self.reason.strip():
            raise ValueError("reason must be a non-empty string")
        if not isinstance(self.improved, bool):
            raise ValueError("improved must be a boolean")
        if (
            not isinstance(self.recovery_attempts, int)
            or isinstance(self.recovery_attempts, bool)
            or self.recovery_attempts < 0
        ):
            raise ValueError(
                "recovery_attempts must be a non-negative integer"
            )

        if (
            not isinstance(self.candidates_tried, Sequence)
            or isinstance(self.candidates_tried, (str, bytes))
        ):
            raise ValueError("candidates_tried must be a sequence")

        candidates = tuple(self.candidates_tried)
        if any(
            not isinstance(candidate, str) or not candidate.strip()
            for candidate in candidates
        ):
            raise ValueError(
                "candidates_tried must contain non-empty model names"
            )

        if self.used != bool(candidates):
            raise ValueError(
                "used must match whether candidates_tried is non-empty"
            )
        if not self.used and self.recovery_attempts != 0:
            raise ValueError(
                "unused recovery cannot report recovery attempts"
            )
        if self.used and self.recovery_attempts < 1:
            raise ValueError(
                "used recovery must report at least one recovery attempt"
            )
        if self.improved and not self.used:
            raise ValueError(
                "improved recovery must have used a recovery candidate"
            )

        best = QualityRecoveryBest.validate(self.best)
        if self.improved and best.model not in candidates:
            raise ValueError(
                "improved best model must appear in candidates_tried"
            )

        if not isinstance(self.details, Mapping):
            raise ValueError("details must be a mapping")

        object.__setattr__(self, "best", best)
        object.__setattr__(self, "candidates_tried", candidates)
        object.__setattr__(self, "details", dict(self.details))

    @classmethod
    def validate(
        cls,
        raw: "QualityRecoveryResult | Mapping[str, Any]",
    ) -> "QualityRecoveryResult":
        if isinstance(raw, cls):
            return raw
        if not isinstance(raw, Mapping):
            raise TypeError(
                "quality recovery result must be a mapping or QualityRecoveryResult"
            )

        required = {
            "used",
            "reason",
            "improved",
            "best",
            "recovery_attempts",
            "candidates_tried",
        }
        missing = sorted(required - set(raw))
        if missing:
            raise ValueError(
                f"quality recovery result missing fields: {', '.join(missing)}"
            )

        raw_candidates = raw["candidates_tried"]
        if (
            not isinstance(raw_candidates, Sequence)
            or isinstance(raw_candidates, (str, bytes))
        ):
            raise ValueError("candidates_tried must be a sequence")

        details = {
            key: value
            for key, value in raw.items()
            if key not in required
        }

        return cls(
            used=raw["used"],
            reason=raw["reason"],
            improved=raw["improved"],
            best=QualityRecoveryBest.validate(raw["best"]),
            recovery_attempts=raw["recovery_attempts"],
            candidates_tried=tuple(raw_candidates),
            details=dict(details),
        )

    def to_dict(self) -> dict[str, Any]:
        return {
            "used": self.used,
            "reason": self.reason,
            "improved": self.improved,
            "best": self.best.to_dict(),
            "recovery_attempts": self.recovery_attempts,
            "candidates_tried": list(self.candidates_tried),
            **dict(self.details),
        }


__all__ = ["QualityRecoveryBest", "QualityRecoveryResult"]
