from dataclasses import dataclass
from typing import Any


@dataclass(frozen=True)
class GroundingContextConsumption:
    """Stable decision describing whether a grounding context may enter execution."""

    status: str
    grounding_status: str
    usable: bool
    reason: str | None = None
    consumption_executed: bool = True

    def __post_init__(self) -> None:
        if self.status not in {"usable", "rejected"}:
            raise ValueError("status must be usable or rejected")
        if self.grounding_status not in {"ready", "not_available", "invalid", "unknown"}:
            raise ValueError("grounding_status must be a supported grounding status")
        if not isinstance(self.usable, bool):
            raise ValueError("usable must be a boolean")
        if not isinstance(self.consumption_executed, bool):
            raise ValueError("consumption_executed must be a boolean")
        if self.status == "usable" and not self.usable:
            raise ValueError("usable status requires usable=True")
        if self.status == "rejected" and self.usable:
            raise ValueError("rejected status requires usable=False")
        if self.reason is not None and (not isinstance(self.reason, str) or not self.reason.strip()):
            raise ValueError("reason must be a nonempty string when provided")

    @classmethod
    def usable_result(cls, grounding_status: str) -> "GroundingContextConsumption":
        return cls(status="usable", grounding_status=grounding_status, usable=True)

    @classmethod
    def rejected_result(
        cls, grounding_status: str, reason: str = "grounding_context_rejected"
    ) -> "GroundingContextConsumption":
        return cls(status="rejected", grounding_status=grounding_status, usable=False, reason=reason)

    def to_dict(self) -> dict[str, Any]:
        return {
            "status": self.status,
            "grounding_status": self.grounding_status,
            "usable": self.usable,
            "reason": self.reason,
            "consumption_executed": self.consumption_executed,
        }


__all__ = ["GroundingContextConsumption"]
