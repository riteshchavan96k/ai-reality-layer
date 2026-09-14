from dataclasses import dataclass
from typing import Any

from backend.app.reality.grounding_context_consumption_result import GroundingContextConsumptionResult


@dataclass(frozen=True)
class GroundingExecutionGateResult:
    """Stable decision contract controlling execution after grounding consumption."""

    status: str
    grounding_status: str
    allowed: bool
    reason: str | None = None
    gate_evaluated: bool = True

    def __post_init__(self) -> None:
        if self.status not in {"allowed", "blocked"}:
            raise ValueError("status must be allowed or blocked")
        if self.grounding_status not in {"ready", "not_available"}:
            raise ValueError("grounding_status must be ready or not_available")
        if not isinstance(self.allowed, bool):
            raise ValueError("allowed must be a boolean")
        if self.status == "allowed" and not self.allowed:
            raise ValueError("allowed status requires allowed=True")
        if self.status == "blocked" and self.allowed:
            raise ValueError("blocked status requires allowed=False")
        if not isinstance(self.gate_evaluated, bool):
            raise ValueError("gate_evaluated must be a boolean")
        if self.reason is not None and (not isinstance(self.reason, str) or not self.reason.strip()):
            raise ValueError("reason must be a nonempty string when provided")

    @classmethod
    def allowed_result(cls, grounding_status: str) -> "GroundingExecutionGateResult":
        return cls(status="allowed", grounding_status=grounding_status, allowed=True)

    @classmethod
    def blocked_result(cls, grounding_status: str, reason: str) -> "GroundingExecutionGateResult":
        return cls(status="blocked", grounding_status=grounding_status, allowed=False, reason=reason)

    def to_dict(self) -> dict[str, Any]:
        return {
            "status": self.status,
            "grounding_status": self.grounding_status,
            "allowed": self.allowed,
            "reason": self.reason,
            "gate_evaluated": self.gate_evaluated,
        }


class GroundingExecutionGate:
    """Decide whether execution may proceed from normalized grounding consumption."""

    def evaluate(self, consumption: GroundingContextConsumptionResult) -> GroundingExecutionGateResult:
        if not isinstance(consumption, GroundingContextConsumptionResult):
            raise ValueError("grounding consumption must be a GroundingContextConsumptionResult")

        if consumption.usable:
            return GroundingExecutionGateResult.allowed_result(consumption.grounding_status)

        return GroundingExecutionGateResult.blocked_result(
            consumption.grounding_status,
            consumption.reason or "grounding_context_rejected",
        )


__all__ = ["GroundingExecutionGate", "GroundingExecutionGateResult"]
