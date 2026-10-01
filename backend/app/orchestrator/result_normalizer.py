from collections.abc import Mapping

from backend.app.orchestrator.result_contract import OrchestrationResult


class OrchestrationResultNormalizer:
    """Normalize terminal orchestration results through the public contract."""

    @staticmethod
    def normalize(raw_result: object) -> OrchestrationResult:
        if isinstance(raw_result, OrchestrationResult):
            return raw_result
        if isinstance(raw_result, Mapping):
            return OrchestrationResult.validate(dict(raw_result))
        raise ValueError(
            "orchestration result must be a contract or mapping"
        )


__all__ = ["OrchestrationResultNormalizer"]
