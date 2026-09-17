from dataclasses import dataclass
from typing import Any

from backend.app.reality.grounding_execution_authorization_consumption_decision import (
    GroundingExecutionAuthorizationConsumptionDecision,
)


@dataclass(frozen=True)
class GroundingExecutionAuthorizationConsumptionDecisionResult:
    """Canonical result contract for the execution-authorization consumption decision."""

    status: str
    authorization_status: str
    allowed: bool
    reason: str | None = None
    decision_executed: bool = True

    def __post_init__(self) -> None:
        if self.status not in {"allowed", "blocked"}:
            raise ValueError("status must be allowed or blocked")
        if self.authorization_status not in {"authorized", "denied"}:
            raise ValueError("authorization_status must be authorized or denied")
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
        if self.authorization_status == "authorized" and not self.allowed:
            raise ValueError("authorized status requires allowed=True")
        if self.authorization_status == "denied" and self.allowed:
            raise ValueError("denied status requires allowed=False")

    @classmethod
    def allowed_result(
        cls,
        authorization_status: str = "authorized",
    ) -> "GroundingExecutionAuthorizationConsumptionDecisionResult":
        return cls("allowed", authorization_status, True)

    @classmethod
    def blocked_result(
        cls,
        authorization_status: str,
        reason: str,
    ) -> "GroundingExecutionAuthorizationConsumptionDecisionResult":
        return cls("blocked", authorization_status, False, reason)

    @classmethod
    def from_decision(
        cls,
        decision: GroundingExecutionAuthorizationConsumptionDecision,
    ) -> "GroundingExecutionAuthorizationConsumptionDecisionResult":
        if not isinstance(decision, GroundingExecutionAuthorizationConsumptionDecision):
            raise ValueError(
                "decision must be a GroundingExecutionAuthorizationConsumptionDecision"
            )
        return cls(
            status=decision.status,
            authorization_status=decision.authorization_status,
            allowed=decision.allowed,
            reason=decision.reason,
            decision_executed=decision.decision_executed,
        )

    def to_dict(self) -> dict[str, Any]:
        return {
            "status": self.status,
            "authorization_status": self.authorization_status,
            "allowed": self.allowed,
            "reason": self.reason,
            "decision_executed": self.decision_executed,
        }


__all__ = ["GroundingExecutionAuthorizationConsumptionDecisionResult"]
