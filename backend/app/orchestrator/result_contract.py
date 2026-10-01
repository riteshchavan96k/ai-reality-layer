from collections.abc import Mapping
from dataclasses import dataclass, field
from typing import Any

from backend.app.evaluation.quality_recovery_normalizer import (
    QualityRecoveryResultNormalizer,
)
from backend.app.evaluation.response_evaluation_normalizer import (
    ResponseEvaluationResultNormalizer,
)
from backend.app.execution.execution_trace_snapshot_normalizer import (
    ExecutionTraceSnapshotNormalizer,
)
from backend.app.execution.model_execution_normalizer import (
    ModelExecutionResultNormalizer,
)
from backend.app.execution.outcome_memory_normalizer import (
    OutcomeMemoryRecordNormalizer,
)
from backend.app.reality.grounded_result_normalizer import (
    GroundedResultEnvelopeNormalizer,
)


_ALLOWED_STATUSES = {
    "awaiting_human_approval",
    "retrieval_unavailable",
    "grounding_unavailable",
    "execution_context_unavailable",
    "execution_failed",
    "orchestrated",
}

_REQUIRED_BY_STATUS = {
    "awaiting_human_approval": {
        "analysis",
        "routing",
        "approval",
        "trace",
    },
    "retrieval_unavailable": {
        "analysis",
        "routing",
        "approval",
        "retrieval",
        "evidence",
        "evidence_quality",
        "grounding",
        "trace",
    },
    "grounding_unavailable": {
        "analysis",
        "routing",
        "approval",
        "retrieval",
        "evidence",
        "evidence_quality",
        "grounding",
        "trace",
    },
    "execution_context_unavailable": {
        "analysis",
        "routing",
        "approval",
        "retrieval",
        "evidence",
        "evidence_quality",
        "grounding",
        "execution_context",
        "trace",
    },
    "execution_failed": {
        "analysis",
        "routing",
        "approval",
        "execution",
        "outcome",
        "trace",
    },
    "orchestrated": {
        "analysis",
        "routing",
        "approval",
        "execution",
        "result",
        "grounding",
        "evaluation",
        "quality_recovery",
        "outcome",
        "trace",
    },
}


def _require_mapping(payload: Mapping[str, Any], name: str) -> dict[str, Any]:
    value = payload[name]
    if not isinstance(value, Mapping):
        raise ValueError(f"{name} must be a mapping")
    return dict(value)


def _validate_execution_summary(raw: object) -> dict[str, Any]:
    if not isinstance(raw, Mapping):
        raise ValueError("execution must be a mapping")

    required = {
        "status",
        "model",
        "attempts",
        "total_attempts",
        "budget_limit",
        "attempts_by_model",
        "fallback_used",
    }
    missing = sorted(required - set(raw))
    if missing:
        raise ValueError(
            f"execution summary missing fields: {', '.join(missing)}"
        )

    if raw["status"] != "success":
        raise ValueError("orchestrated execution summary must have success status")
    if not isinstance(raw["model"], str) or not raw["model"].strip():
        raise ValueError("orchestrated execution summary requires a model")

    for name in ("attempts", "total_attempts", "budget_limit"):
        value = raw[name]
        if (
            not isinstance(value, int)
            or isinstance(value, bool)
            or value < 0
        ):
            raise ValueError(f"{name} must be a non-negative integer")

    if raw["budget_limit"] < 1:
        raise ValueError("budget_limit must be at least 1")
    if raw["attempts"] > raw["total_attempts"]:
        raise ValueError("attempts cannot exceed total_attempts")
    if raw["total_attempts"] > raw["budget_limit"]:
        raise ValueError("total_attempts cannot exceed budget_limit")

    attempts_by_model = raw["attempts_by_model"]
    if not isinstance(attempts_by_model, Mapping):
        raise ValueError("attempts_by_model must be a mapping")
    normalized_attempts: dict[str, int] = {}
    for model, count in attempts_by_model.items():
        if (
            not isinstance(model, str)
            or not model.strip()
            or not isinstance(count, int)
            or isinstance(count, bool)
            or count < 0
        ):
            raise ValueError(
                "attempts_by_model must map non-empty model names to non-negative integers"
            )
        normalized_attempts[model] = count
    if sum(normalized_attempts.values()) != raw["total_attempts"]:
        raise ValueError(
            "attempts_by_model counts must equal total_attempts"
        )

    if not isinstance(raw["fallback_used"], bool):
        raise ValueError("fallback_used must be a boolean")

    return {
        **dict(raw),
        "attempts_by_model": normalized_attempts,
    }


@dataclass(frozen=True)
class OrchestrationResult:
    """Canonical public envelope returned by the orchestration pipeline."""

    status: str
    payload: dict[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        if self.status not in _ALLOWED_STATUSES:
            raise ValueError(
                "status must be a supported orchestration terminal status"
            )
        if not isinstance(self.payload, Mapping):
            raise ValueError("payload must be a mapping")

        payload = dict(self.payload)
        required = _REQUIRED_BY_STATUS[self.status]
        missing = sorted(required - set(payload))
        if missing:
            raise ValueError(
                f"{self.status} orchestration result missing fields: {', '.join(missing)}"
            )

        for name in ("analysis", "routing", "approval"):
            _require_mapping(payload, name)

        trace = ExecutionTraceSnapshotNormalizer.normalize(
            payload["trace"]
        ).to_list()
        payload["trace"] = trace

        if self.status in {
            "retrieval_unavailable",
            "grounding_unavailable",
            "execution_context_unavailable",
        }:
            for name in (
                "retrieval",
                "evidence",
                "evidence_quality",
                "grounding",
            ):
                _require_mapping(payload, name)

        if self.status == "retrieval_unavailable":
            payload["grounding"] = (
                GroundedResultEnvelopeNormalizer.normalize(
                    payload["grounding"]
                ).to_dict()
            )

        if self.status == "execution_context_unavailable":
            _require_mapping(payload, "execution_context")

        if self.status == "execution_failed":
            execution = ModelExecutionResultNormalizer.normalize(
                payload["execution"]
            )
            if execution.status != "failed":
                raise ValueError(
                    "execution_failed result requires failed execution"
                )
            payload["execution"] = execution.to_dict()

            outcome = OutcomeMemoryRecordNormalizer.normalize(
                payload["outcome"]
            )
            if outcome.execution_status != "failed":
                raise ValueError(
                    "execution_failed result requires failed outcome record"
                )
            payload["outcome"] = outcome.to_dict()

        if self.status == "orchestrated":
            payload["execution"] = _validate_execution_summary(
                payload["execution"]
            )
            if not isinstance(payload["result"], Mapping):
                raise ValueError("orchestrated result must be a mapping")
            payload["result"] = dict(payload["result"])

            payload["grounding"] = (
                GroundedResultEnvelopeNormalizer.normalize(
                    payload["grounding"]
                ).to_dict()
            )
            payload["evaluation"] = (
                ResponseEvaluationResultNormalizer.normalize(
                    payload["evaluation"]
                ).to_dict()
            )
            payload["quality_recovery"] = (
                QualityRecoveryResultNormalizer.normalize(
                    payload["quality_recovery"]
                ).to_dict()
            )
            payload["outcome"] = (
                OutcomeMemoryRecordNormalizer.normalize(
                    payload["outcome"]
                ).to_dict()
            )

            if payload["outcome"]["execution_status"] != "success":
                raise ValueError(
                    "orchestrated result requires successful outcome record"
                )
            if (
                payload["outcome"]["executed_model"]
                != payload["execution"]["model"]
            ):
                raise ValueError(
                    "outcome executed_model must match orchestration execution model"
                )
            if (
                payload["outcome"]["evaluation_score"]
                != payload["evaluation"]["score"]
            ):
                raise ValueError(
                    "outcome evaluation_score must match orchestration evaluation score"
                )

        object.__setattr__(self, "payload", payload)

    @classmethod
    def validate(
        cls,
        raw: "OrchestrationResult | Mapping[str, Any]",
    ) -> "OrchestrationResult":
        if isinstance(raw, cls):
            return raw
        if not isinstance(raw, Mapping):
            raise TypeError(
                "orchestration result must be a mapping or OrchestrationResult"
            )
        if "status" not in raw:
            raise ValueError("orchestration result missing field: status")

        payload = {
            key: value
            for key, value in raw.items()
            if key != "status"
        }
        return cls(
            status=raw["status"],
            payload=payload,
        )

    def to_dict(self) -> dict[str, Any]:
        return {
            "status": self.status,
            **dict(self.payload),
        }


__all__ = ["OrchestrationResult"]
