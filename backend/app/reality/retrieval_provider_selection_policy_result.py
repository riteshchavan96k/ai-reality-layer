from dataclasses import dataclass
from typing import Any


@dataclass(frozen=True)
class RetrievalProviderSelectionPolicyResult:
    """Stable result contract for the combined provider-selection policy decision."""

    status: str
    source_type: str
    allowed: bool
    reason: str | None = None
    policy_evaluated: bool = True

    def __post_init__(self) -> None:
        if self.status not in {"allowed", "rejected"}:
            raise ValueError("status must be allowed or rejected")
        if not isinstance(self.source_type, str) or not self.source_type.strip():
            raise ValueError("source_type must be a nonempty string")
        if not isinstance(self.allowed, bool):
            raise ValueError("allowed must be a boolean")
        if not isinstance(self.policy_evaluated, bool):
            raise ValueError("policy_evaluated must be a boolean")
        if self.status == "allowed" and not self.allowed:
            raise ValueError("allowed status requires allowed=True")
        if self.status == "rejected" and self.allowed:
            raise ValueError("rejected status requires allowed=False")
        if self.reason is not None and (not isinstance(self.reason, str) or not self.reason.strip()):
            raise ValueError("reason must be a nonempty string when provided")

    @classmethod
    def allowed_result(cls, source_type: str) -> "RetrievalProviderSelectionPolicyResult":
        return cls(status="allowed", source_type=source_type, allowed=True)

    @classmethod
    def rejected_result(
        cls,
        source_type: str,
        reason: str = "retrieval_provider_selection_policy_rejected",
    ) -> "RetrievalProviderSelectionPolicyResult":
        return cls(status="rejected", source_type=source_type, allowed=False, reason=reason)

    def to_dict(self) -> dict[str, Any]:
        return {
            "status": self.status,
            "source_type": self.source_type,
            "allowed": self.allowed,
            "reason": self.reason,
            "policy_evaluated": self.policy_evaluated,
        }


__all__ = ["RetrievalProviderSelectionPolicyResult"]
