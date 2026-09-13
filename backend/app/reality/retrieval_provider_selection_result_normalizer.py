from collections.abc import Mapping
from typing import Any

from backend.app.reality.retrieval_provider_selection import RetrievalProviderSelectionResult
from backend.app.reality.retrieval_provider_selection_decision import RetrievalProviderSelectionDecision
from backend.app.reality.retrieval_provider_selection_decision_normalizer import (
    RetrievalProviderSelectionDecisionNormalizer,
)


class RetrievalProviderSelectionResultNormalizer:
    """Normalize typed or legacy selection-result mappings into the canonical result contract."""

    @staticmethod
    def normalize(raw_result: object) -> RetrievalProviderSelectionResult:
        if isinstance(raw_result, RetrievalProviderSelectionResult):
            return raw_result

        if isinstance(raw_result, Mapping):
            values: dict[str, Any] = dict(raw_result)
            decision = values.get("decision")
            if decision is not None:
                decision = RetrievalProviderSelectionDecisionNormalizer.normalize(decision)
                values["decision"] = decision

            return RetrievalProviderSelectionResult(
                status=values["status"],
                source_type=values["source_type"],
                provider=values.get("provider"),
                reason=values.get("reason"),
                decision=values.get("decision"),
            )

        raise ValueError(
            "retrieval provider selection result must be a result contract or mapping"
        )


__all__ = ["RetrievalProviderSelectionResultNormalizer"]
