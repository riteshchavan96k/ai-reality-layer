from dataclasses import dataclass
from typing import Any


@dataclass(frozen=True)
class RetrievalResultConsumption:
    """Stable decision describing whether a retrieval result may enter evidence processing."""

    status: str
    retrieval_status: str
    usable: bool
    reason: str | None = None
    consumption_executed: bool = True

    def __post_init__(self) -> None:
        if self.status not in {"usable", "rejected"}:
            raise ValueError("status must be usable or rejected")
        if self.retrieval_status not in {"completed", "failed", "blocked", "not_required"}:
            raise ValueError("retrieval_status must be a supported retrieval status")
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
    def usable_result(cls, retrieval_status: str = "completed") -> "RetrievalResultConsumption":
        return cls(status="usable", retrieval_status=retrieval_status, usable=True)

    @classmethod
    def rejected_result(cls, retrieval_status: str, reason: str) -> "RetrievalResultConsumption":
        return cls(status="rejected", retrieval_status=retrieval_status, usable=False, reason=reason)

    def to_dict(self) -> dict[str, Any]:
        return {
            "status": self.status,
            "retrieval_status": self.retrieval_status,
            "usable": self.usable,
            "reason": self.reason,
            "consumption_executed": self.consumption_executed,
        }


__all__ = ["RetrievalResultConsumption"]
