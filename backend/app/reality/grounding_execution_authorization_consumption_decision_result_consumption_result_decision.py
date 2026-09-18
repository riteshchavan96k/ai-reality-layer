from dataclasses import dataclass

from backend.app.reality.grounding_execution_authorization_consumption_decision_result_consumption_result import (
    GroundingExecutionAuthorizationConsumptionDecisionResultConsumptionResult,
)


@dataclass(frozen=True)
class GroundingExecutionAuthorizationConsumptionDecisionResultConsumptionResultDecision:
    """Canonical execution decision derived from the consumed authorization decision result."""

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
    ) -> "GroundingExecutionAuthorizationConsumptionDecisionResultConsumptionResultDecision":
        return cls("allowed", authorization_status, True)

    @classmethod
    def blocked_result(
        cls,
        authorization_status: str,
        reason: str,
    ) -> "GroundingExecutionAuthorizationConsumptionDecisionResultConsumptionResultDecision":
        return cls("blocked", authorization_status, False, reason)

    @classmethod
    def from_consumption_result(
        cls,
        consumption_result: GroundingExecutionAuthorizationConsumptionDecisionResultConsumptionResult,
    ) -> "GroundingExecutionAuthorizationConsumptionDecisionResultConsumptionResultDecision":
        if not isinstance(
            consumption_result,
            GroundingExecutionAuthorizationConsumptionDecisionResultConsumptionResult,
        ):
            raise ValueError(
                "consumption_result must be a GroundingExecutionAuthorizationConsumptionDecisionResultConsumptionResult"
            )
        if not consumption_result.decision_executed:
            raise ValueError("decision result consumption requires decision_executed=True")
        if not consumption_result.consumption_executed:
            raise ValueError("decision result consumption requires consumption_executed=True")
        if consumption_result.allowed:
            return cls.allowed_result(consumption_result.authorization_status)
        return cls.blocked_result(
            consumption_result.authorization_status,
            consumption_result.reason or "execution_authorization_decision_result_consumption_rejected",
        )

    def to_dict(self) -> dict[str, object]:
        return {
            "status": self.status,
            "authorization_status": self.authorization_status,
            "allowed": self.allowed,
            "reason": self.reason,
            "decision_executed": self.decision_executed,
        }


__all__ = [
    "GroundingExecutionAuthorizationConsumptionDecisionResultConsumptionResultDecision",
]
