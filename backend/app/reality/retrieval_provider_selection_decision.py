from dataclasses import dataclass
from typing import Any

from backend.app.reality.retrieval_provider_selection_policy_result import RetrievalProviderSelectionPolicyResult


@dataclass(frozen=True)
class RetrievalProviderSelectionDecision:
    """Stable decision record produced after the provider-selection policy is evaluated."""

    status: str
    source_type: str
    provider: Any | None = None
    reason: str | None = None
    policy_result: RetrievalProviderSelectionPolicyResult | None = None
    selection_decided: bool = True

    def __post_init__(self) -> None:
        if self.status not in {"selected", "rejected"}:
            raise ValueError("status must be selected or rejected")
        if not isinstance(self.source_type, str) or not self.source_type.strip():
            raise ValueError("source_type must be a nonempty string")
        if not isinstance(self.selection_decided, bool):
            raise ValueError("selection_decided must be a boolean")
        if self.status == "selected" and self.provider is None:
            raise ValueError("selected status requires a provider")
        if self.status == "rejected" and self.provider is not None:
            raise ValueError("rejected status cannot contain a provider")
        if self.reason is not None and (not isinstance(self.reason, str) or not self.reason.strip()):
            raise ValueError("reason must be a nonempty string when provided")
        if self.policy_result is not None and not isinstance(
            self.policy_result, RetrievalProviderSelectionPolicyResult
        ):
            raise ValueError(
                "policy_result must be a RetrievalProviderSelectionPolicyResult or None"
            )

    @classmethod
    def selected(cls, source_type: str, provider: Any, policy_result=None):
        return cls("selected", source_type, provider=provider, policy_result=policy_result)

    @classmethod
    def rejected(cls, source_type: str, reason: str, policy_result=None):
        return cls("rejected", source_type, reason=reason, policy_result=policy_result)

    def to_dict(self) -> dict[str, Any]:
        return {
            "status": self.status,
            "source_type": self.source_type,
            "provider": self.provider,
            "reason": self.reason,
            "policy_result": self.policy_result.to_dict() if self.policy_result else None,
            "selection_decided": self.selection_decided,
        }


__all__ = ["RetrievalProviderSelectionDecision"]
