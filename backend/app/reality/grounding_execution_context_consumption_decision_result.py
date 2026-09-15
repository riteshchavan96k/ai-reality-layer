from dataclasses import dataclass
from typing import Any

from backend.app.reality.grounding_execution_context_consumption_decision import (
    GroundingExecutionContextConsumptionDecision,
)


@dataclass(frozen=True)
class GroundingExecutionContextConsumptionDecisionResult:
    """Canonical result contract for the execution-context consumption decision."""

    status: str
    grounding_status: str
    allowed: bool
    reason: str | None = None
    decision_executed: bool = True

    def __post_init__(self) -> None:
        if self.status not in {"allowed", "blocked"}:
            raise ValueError("status must be allowed or blocked")
        if self.grounding_status not in {"ready", "not_available"}:
            raise ValueError("grounding_status must be ready or not_available")
        if not isinstance(self.allowed, bool):
            raise ValueError("allowed must be a boolean")
        if not isinstance(self.decision_executed, bool):
            raise ValueError("decision_executed must be a boolean")
        if self.status == "allowed" and not self.allowed:
            raise ValueError("allowed status requires allowed=True")
        if self.status == "blocked" and self.allowed:
            raise ValueError("blocked status requires allowed=False")
        if self.allowed and self.reason is not None:
            raise ValueError("allowed decision cannot contain a reason")
        if not self.allowed and (not isinstance(self.reason, str) or not self.reason.strip()):
            raise ValueError("blocked decision requires a reason")

    @classmethod
    def allowed_result(cls, grounding_status: str) -> "GroundingExecutionContextConsumptionDecisionResult":
        return cls("allowed", grounding_status, True)

    @classmethod
    def blocked_result(cls, grounding_status: str, reason: str) -> "GroundingExecutionContextConsumptionDecisionResult":
        return cls("blocked", grounding_status, False, reason)

    @classmethod
    def from_decision(
        cls, decision: GroundingExecutionContextConsumptionDecision
    ) -> "GroundingExecutionContextConsumptionDecisionResult":
        if not isinstance(decision, GroundingExecutionContextConsumptionDecision):
            raise ValueError("decision must be a GroundingExecutionContextConsumptionDecision")
        return cls(
            status=decision.status,
            grounding_status=decision.grounding_status,
            allowed=decision.allowed,
            reason=decision.reason,
            decision_executed=decision.decision_executed,
        )

    def to_dict(self) -> dict[str, Any]:
        return {
            "status": self.status,
            "grounding_status": self.grounding_status,
            "allowed": self.allowed,
            "reason": self.reason,
            "decision_executed": self.decision_executed,
        }


__all__ = ["GroundingExecutionContextConsumptionDecisionResult"]
