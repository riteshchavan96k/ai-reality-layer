from collections.abc import Mapping
from typing import Any

from backend.app.reality.retrieval_result_consumption import RetrievalResultConsumption


class RetrievalResultConsumptionNormalizer:
    """Normalize typed or legacy consumption decisions into the canonical contract."""

    @staticmethod
    def normalize(raw_consumption: object) -> RetrievalResultConsumption:
        if isinstance(raw_consumption, RetrievalResultConsumption):
            return raw_consumption

        if isinstance(raw_consumption, Mapping):
            values: dict[str, Any] = dict(raw_consumption)
            return RetrievalResultConsumption(
                status=values["status"],
                retrieval_status=values["retrieval_status"],
                usable=values["usable"],
                reason=values.get("reason"),
                consumption_executed=values.get("consumption_executed", True),
            )

        raise ValueError(
            "retrieval result consumption must be a consumption contract or mapping"
        )


__all__ = ["RetrievalResultConsumptionNormalizer"]
