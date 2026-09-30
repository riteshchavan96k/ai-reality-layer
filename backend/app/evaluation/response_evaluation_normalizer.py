from collections.abc import Mapping

from backend.app.evaluation.response_evaluation_contract import (
    ResponseEvaluationResult,
)


class ResponseEvaluationResultNormalizer:
    """Normalize response-evaluation outcomes through the canonical contract."""

    @staticmethod
    def normalize(raw_result: object) -> ResponseEvaluationResult:
        if isinstance(raw_result, ResponseEvaluationResult):
            return raw_result
        if isinstance(raw_result, Mapping):
            return ResponseEvaluationResult.validate(dict(raw_result))
        raise ValueError(
            "response evaluation result must be a contract or mapping"
        )


__all__ = ["ResponseEvaluationResultNormalizer"]
