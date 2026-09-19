from collections.abc import Mapping

from backend.app.reality.retrieval_result_consumption import RetrievalResultConsumption


class RetrievalResultConsumptionNormalizer:
    """Normalize typed or legacy consumption decisions into the canonical contract."""

    @staticmethod
    def normalize(raw_consumption: object) -> RetrievalResultConsumption:
        if isinstance(raw_consumption, RetrievalResultConsumption):
            return raw_consumption

        if isinstance(raw_consumption, Mapping):
            return RetrievalResultConsumption.validate(dict(raw_consumption))

        raise ValueError(
            "retrieval result consumption must be a consumption contract or mapping"
        )


__all__ = ["RetrievalResultConsumptionNormalizer"]
