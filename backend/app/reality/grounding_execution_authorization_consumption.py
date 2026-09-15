from dataclasses import dataclass
from typing import Any


@dataclass(frozen=True)
class GroundingExecutionAuthorizationConsumption:
    """Canonical consumption result for grounding execution authorization."""

    status: str
    authorization_status: str
    usable: bool
    reason: str | None = None
    consumption_executed: bool = True

    def __post_init__(self) -> None:
        if self.status not in {"usable", "rejected"}:
            raise ValueError("status must be usable or rejected")
        if self.authorization_status not in {"authorized", "denied"}:
            raise ValueError("authorization_status must be authorized or denied")
        if not isinstance(self.usable, bool):
            raise ValueError("usable must be a boolean")
        if not isinstance(self.consumption_executed, bool):
            raise ValueError("consumption_executed must be a boolean")
        if self.status == "usable" and not self.usable:
            raise ValueError("usable status requires usable=True")
        if self.status == "rejected" and self.usable:
            raise ValueError("rejected status requires usable=False")
        if self.usable and self.reason is not None:
            raise ValueError("usable authorization consumption cannot contain a reason")
        if not self.usable and (not isinstance(self.reason, str) or not self.reason.strip()):
            raise ValueError("rejected authorization consumption requires a reason")
        if self.authorization_status == "authorized" and not self.usable:
            raise ValueError("authorized status requires usable=True")
        if self.authorization_status == "denied" and self.usable:
            raise ValueError("denied status requires usable=False")

    @classmethod
    def usable_result(cls, authorization_status: str = "authorized", consumption_executed: bool = True) -> "GroundingExecutionAuthorizationConsumption":
        return cls("usable", authorization_status, True, consumption_executed=consumption_executed)

    @classmethod
    def rejected_result(cls, authorization_status: str, reason: str, consumption_executed: bool = True) -> "GroundingExecutionAuthorizationConsumption":
        return cls("rejected", authorization_status, False, reason, consumption_executed)

    def to_dict(self) -> dict[str, Any]:
        return {
            "status": self.status,
            "authorization_status": self.authorization_status,
            "usable": self.usable,
            "reason": self.reason,
            "consumption_executed": self.consumption_executed,
        }


__all__ = ["GroundingExecutionAuthorizationConsumption"]
