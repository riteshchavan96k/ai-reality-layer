from dataclasses import dataclass

from backend.app.reality.grounding_execution_context_consumption_result import (
    GroundingExecutionContextConsumptionResult,
)


@dataclass(frozen=True)
class GroundingExecutionContextConsumptionDecision:
    """Canonical decision derived from an execution-context consumption result."""

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
    def allowed_result(cls, grounding_status: str) -> "GroundingExecutionContextConsumptionDecision":
        return cls("allowed", grounding_status, True)

    @classmethod
    def blocked_result(cls, grounding_status: str, reason: str) -> "GroundingExecutionContextConsumptionDecision":
        return cls("blocked", grounding_status, False, reason)

    @classmethod
    def from_consumption(
        cls, consumption: GroundingExecutionContextConsumptionResult
    ) -> "GroundingExecutionContextConsumptionDecision":
        if not isinstance(consumption, GroundingExecutionContextConsumptionResult):
            raise ValueError("consumption must be a GroundingExecutionContextConsumptionResult")
        if consumption.usable:
            return cls.allowed_result(consumption.grounding_status)
        return cls.blocked_result(consumption.grounding_status, consumption.reason or "execution_context_consumption_rejected")

    def to_dict(self) -> dict[str, object]:
        return {
            "status": self.status,
            "grounding_status": self.grounding_status,
            "allowed": self.allowed,
            "reason": self.reason,
            "decision_executed": self.decision_executed,
        }


__all__ = ["GroundingExecutionContextConsumptionDecision"]
