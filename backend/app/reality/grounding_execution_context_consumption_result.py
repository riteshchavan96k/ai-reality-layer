from dataclasses import dataclass


@dataclass(frozen=True)
class GroundingExecutionContextConsumptionResult:
    """Canonical result produced when an execution context is consumed."""

    status: str
    grounding_status: str
    usable: bool
    reason: str | None = None
    consumption_executed: bool = True

    def __post_init__(self) -> None:
        if self.status not in {"usable", "rejected"}:
            raise ValueError("status must be usable or rejected")
        if self.grounding_status not in {"ready", "not_available"}:
            raise ValueError("grounding_status must be ready or not_available")
        if not isinstance(self.usable, bool):
            raise ValueError("usable must be a boolean")
        if not isinstance(self.consumption_executed, bool):
            raise ValueError("consumption_executed must be a boolean")
        if self.status == "usable" and not self.usable:
            raise ValueError("usable status requires usable=True")
        if self.status == "rejected" and self.usable:
            raise ValueError("rejected status requires usable=False")
        if self.usable and self.reason is not None:
            raise ValueError("usable context consumption cannot contain a reason")
        if not self.usable and (not isinstance(self.reason, str) or not self.reason.strip()):
            raise ValueError("rejected context consumption requires a reason")

    @classmethod
    def usable_result(cls, grounding_status: str) -> "GroundingExecutionContextConsumptionResult":
        return cls("usable", grounding_status, True)

    @classmethod
    def rejected_result(cls, grounding_status: str, reason: str) -> "GroundingExecutionContextConsumptionResult":
        return cls("rejected", grounding_status, False, reason)

    def to_dict(self) -> dict[str, object]:
        return {
            "status": self.status,
            "grounding_status": self.grounding_status,
            "usable": self.usable,
            "reason": self.reason,
            "consumption_executed": self.consumption_executed,
        }


__all__ = ["GroundingExecutionContextConsumptionResult"]
