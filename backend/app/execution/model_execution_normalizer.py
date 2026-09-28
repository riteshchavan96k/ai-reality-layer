from collections.abc import Mapping

from backend.app.execution.model_execution_contract import ModelExecutionResult


class ModelExecutionResultNormalizer:
    """Normalize model execution outcomes through the canonical contract."""

    @staticmethod
    def normalize(raw_result: object) -> ModelExecutionResult:
        if isinstance(raw_result, ModelExecutionResult):
            return raw_result
        if isinstance(raw_result, Mapping):
            return ModelExecutionResult.validate(dict(raw_result))
        raise ValueError("model execution result must be a contract or mapping")


__all__ = ["ModelExecutionResultNormalizer"]
