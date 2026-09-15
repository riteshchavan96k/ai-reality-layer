from dataclasses import dataclass
from typing import Any

from backend.app.reality.grounding_execution_context_consumption_decision_result import (
    GroundingExecutionContextConsumptionDecisionResult,
)


@dataclass(frozen=True)
class GroundingExecutionAuthorization:
    """Canonical authorization to enter model execution from grounded context."""

    status: str
    grounding_status: str
    authorized: bool
    reason: str | None = None
    authorization_executed: bool = True

    def __post_init__(self) -> None:
        if self.status not in {"authorized", "denied"}:
            raise ValueError("status must be authorized or denied")
        if self.grounding_status not in {"ready", "not_available"}:
            raise ValueError("grounding_status must be ready or not_available")
        if not isinstance(self.authorized, bool):
            raise ValueError("authorized must be a boolean")
        if not isinstance(self.authorization_executed, bool):
            raise ValueError("authorization_executed must be a boolean")
        if self.status == "authorized" and not self.authorized:
            raise ValueError("authorized status requires authorized=True")
        if self.status == "denied" and self.authorized:
            raise ValueError("denied status requires authorized=False")
        if self.authorized and self.reason is not None:
            raise ValueError("authorized result cannot contain a reason")
        if not self.authorized and (not isinstance(self.reason, str) or not self.reason.strip()):
            raise ValueError("denied authorization requires a reason")

    @classmethod
    def authorized_result(cls, grounding_status: str) -> "GroundingExecutionAuthorization":
        return cls("authorized", grounding_status, True)

    @classmethod
    def denied_result(cls, grounding_status: str, reason: str) -> "GroundingExecutionAuthorization":
        return cls("denied", grounding_status, False, reason)

    @classmethod
    def from_decision_result(
        cls, decision_result: GroundingExecutionContextConsumptionDecisionResult
    ) -> "GroundingExecutionAuthorization":
        if not isinstance(decision_result, GroundingExecutionContextConsumptionDecisionResult):
            raise ValueError(
                "decision_result must be a GroundingExecutionContextConsumptionDecisionResult"
            )
        if decision_result.allowed:
            return cls.authorized_result(decision_result.grounding_status)
        return cls.denied_result(
            decision_result.grounding_status,
            decision_result.reason or "execution_authorization_denied",
        )

    def to_dict(self) -> dict[str, Any]:
        return {
            "status": self.status,
            "grounding_status": self.grounding_status,
            "authorized": self.authorized,
            "reason": self.reason,
            "authorization_executed": self.authorization_executed,
        }


__all__ = ["GroundingExecutionAuthorization"]
