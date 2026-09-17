from dataclasses import dataclass
from typing import Any


@dataclass(frozen=True)
class GroundingExecutionAuthorizationConsumptionDecisionResultConsumptionResult:
    """Canonical result produced when the authorization decision result is consumed."""

    status: str
    authorization_status: str
    allowed: bool
    reason: str | None = None
    decision_executed: bool = True
    consumption_executed: bool = True

    def __post_init__(self) -> None:
        if self.status not in {"usable", "rejected"}:
            raise ValueError("status must be usable or rejected")
        if self.authorization_status not in {"authorized", "denied"}:
            raise ValueError("authorization_status must be authorized or denied")
        if not isinstance(self.allowed, bool):
            raise ValueError("allowed must be a boolean")
        if not isinstance(self.decision_executed, bool):
            raise ValueError("decision_executed must be a boolean")
        if not isinstance(self.consumption_executed, bool):
            raise ValueError("consumption_executed must be a boolean")
        if self.status == "usable" and not self.allowed:
            raise ValueError("usable status requires allowed=True")
        if self.status == "rejected" and self.allowed:
            raise ValueError("rejected status requires allowed=False")
        if self.allowed and self.reason is not None:
            raise ValueError("usable authorization decision result consumption cannot contain a reason")
        if not self.allowed and (not isinstance(self.reason, str) or not self.reason.strip()):
            raise ValueError("rejected authorization decision result consumption requires a reason")
        if self.authorization_status == "authorized" and not self.allowed:
            raise ValueError("authorized status requires allowed=True")
        if self.authorization_status == "denied" and self.allowed:
            raise ValueError("denied status requires allowed=False")
        if not self.decision_executed:
            raise ValueError("decision result consumption requires decision_executed=True")
        if not self.consumption_executed:
            raise ValueError("decision result consumption requires consumption_executed=True")

    @classmethod
    def usable_result(
        cls,
        authorization_status: str = "authorized",
        decision_executed: bool = True,
        consumption_executed: bool = True,
    ) -> "GroundingExecutionAuthorizationConsumptionDecisionResultConsumptionResult":
        return cls(
            "usable",
            authorization_status,
            True,
            decision_executed=decision_executed,
            consumption_executed=consumption_executed,
        )

    @classmethod
    def rejected_result(
        cls,
        authorization_status: str,
        reason: str,
        decision_executed: bool = True,
        consumption_executed: bool = True,
    ) -> "GroundingExecutionAuthorizationConsumptionDecisionResultConsumptionResult":
        return cls(
            "rejected",
            authorization_status,
            False,
            reason,
            decision_executed,
            consumption_executed,
        )

    def to_dict(self) -> dict[str, Any]:
        return {
            "status": self.status,
            "authorization_status": self.authorization_status,
            "allowed": self.allowed,
            "reason": self.reason,
            "decision_executed": self.decision_executed,
            "consumption_executed": self.consumption_executed,
        }


__all__ = [
    "GroundingExecutionAuthorizationConsumptionDecisionResultConsumptionResult",
]
