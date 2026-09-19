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

    @classmethod
    def validate(cls, result: object) -> "RetrievalResultConsumption":
        """Validate an existing consumption decision at the downstream boundary."""
        if isinstance(result, cls):
            return result

        if not isinstance(result, dict):
            raise ValueError("retrieval result consumption must be a dictionary")

        required = {
            "status",
            "retrieval_status",
            "usable",
            "consumption_executed",
        }
        if not required.issubset(result):
            raise ValueError("retrieval result consumption is missing required fields")

        return cls(
            status=result["status"],
            retrieval_status=result["retrieval_status"],
            usable=result["usable"],
            reason=result.get("reason"),
            consumption_executed=result["consumption_executed"],
        )

    def to_dict(self) -> dict[str, Any]:
        return {
            "status": self.status,
            "retrieval_status": self.retrieval_status,
            "usable": self.usable,
            "reason": self.reason,
            "consumption_executed": self.consumption_executed,
        }


__all__ = ["RetrievalResultConsumption"]
