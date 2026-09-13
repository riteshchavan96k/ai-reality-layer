from collections.abc import Mapping
from typing import Any

from backend.app.reality.retrieval_provider_selection_decision import RetrievalProviderSelectionDecision
from backend.app.reality.retrieval_provider_selection_policy_result import RetrievalProviderSelectionPolicyResult


class RetrievalProviderSelectionDecisionNormalizer:
    """Normalize typed or legacy decision mappings into the canonical decision contract."""

    @staticmethod
    def normalize(raw_decision: object) -> RetrievalProviderSelectionDecision:
        if isinstance(raw_decision, RetrievalProviderSelectionDecision):
            return raw_decision

        if isinstance(raw_decision, Mapping):
            values: dict[str, Any] = dict(raw_decision)
            policy_result = values.get("policy_result")
            if isinstance(policy_result, Mapping):
                policy_result = RetrievalProviderSelectionPolicyResult(
                    status=policy_result["status"],
                    source_type=policy_result["source_type"],
                    allowed=policy_result["allowed"],
                    reason=policy_result.get("reason"),
                    policy_evaluated=policy_result.get("policy_evaluated", True),
                )
                values["policy_result"] = policy_result
            return RetrievalProviderSelectionDecision(
                status=values["status"],
                source_type=values["source_type"],
                provider=values.get("provider"),
                reason=values.get("reason"),
                policy_result=values.get("policy_result"),
                selection_decided=values.get("selection_decided", True),
            )

        raise ValueError("retrieval provider selection decision must be a decision contract or mapping")


__all__ = ["RetrievalProviderSelectionDecisionNormalizer"]
