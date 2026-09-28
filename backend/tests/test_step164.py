import pytest

from backend.app.execution.fallback_executor import execute_with_fallback
from backend.app.execution.execution_budget import ExecutionBudget
from backend.app.execution.model_execution_contract import ModelExecutionResult
from backend.app.execution.model_execution_normalizer import ModelExecutionResultNormalizer
from backend.app.execution.retry_policy import RetryPolicy


def test_step164_accepts_success_result():
    result = ModelExecutionResult(
        status="success",
        model="model-a",
        attempts=1,
        total_attempts=1,
        budget_limit=2,
        attempts_by_model={"model-a": 1},
        fallback_used=False,
        result={"text": "answer", "model": "model-a", "provider": "test"},
    )

    assert ModelExecutionResult.validate(result) is result


def test_step164_normalizes_mapping():
    result = ModelExecutionResultNormalizer.normalize(
        {
            "status": "failed",
            "model": None,
            "attempts": 1,
            "total_attempts": 1,
            "budget_limit": 2,
            "attempts_by_model": {"model-a": 1},
            "fallback_used": False,
            "result": None,
            "errors": {"model-a": "provider_execution_failed"},
        }
    )

    assert isinstance(result, ModelExecutionResult)
    assert result.status == "failed"
    assert result.total_attempts == 1


def test_step164_rejects_missing_required_field():
    with pytest.raises(ValueError, match="missing required fields"):
        ModelExecutionResult.validate(
            {
                "status": "success",
                "model": "model-a",
                "attempts": 1,
                "total_attempts": 1,
                "budget_limit": 2,
                "attempts_by_model": {"model-a": 1},
                "fallback_used": False,
                "result": {"text": "answer"},
            }
        )


def test_step164_rejects_attempt_count_mismatch():
    with pytest.raises(ValueError, match="attempts_by_model counts must equal total_attempts"):
        ModelExecutionResultNormalizer.normalize(
            {
                "status": "failed",
                "model": None,
                "attempts": 1,
                "total_attempts": 2,
                "budget_limit": 3,
                "attempts_by_model": {"model-a": 1},
                "fallback_used": False,
                "result": None,
                "errors": {"model-a": "failed"},
            }
        )


def test_step164_rejects_success_without_result():
    with pytest.raises(ValueError, match="successful execution requires a result mapping"):
        ModelExecutionResultNormalizer.normalize(
            {
                "status": "success",
                "model": "model-a",
                "attempts": 1,
                "total_attempts": 1,
                "budget_limit": 2,
                "attempts_by_model": {"model-a": 1},
                "fallback_used": False,
                "result": None,
                "errors": None,
            }
        )


def test_step164_fallback_executor_returns_canonical_success_result():
    class Adapter:
        def generate(self, task, context=None):
            return {"text": "answer", "provider": "test-provider"}

    result = execute_with_fallback(
        task="test task",
        model_names=["model-a"],
        adapter_resolver=lambda name: Adapter(),
        retry_policy=RetryPolicy(max_attempts=1),
        execution_budget=ExecutionBudget(max_attempts=1),
    )

    validated = ModelExecutionResult.validate(result)
    assert validated.status == "success"
    assert validated.model == "model-a"
    assert validated.total_attempts == 1
    assert validated.result["text"] == "answer"


def test_step164_fallback_executor_returns_canonical_failure_result():
    class Adapter:
        def generate(self, task, context=None):
            raise RuntimeError("provider failed")

    result = execute_with_fallback(
        task="test task",
        model_names=["model-a"],
        adapter_resolver=lambda name: Adapter(),
        retry_policy=RetryPolicy(max_attempts=1),
        execution_budget=ExecutionBudget(max_attempts=1),
    )

    validated = ModelExecutionResult.validate(result)
    assert validated.status == "failed"
    assert validated.model is None
    assert validated.total_attempts == 1
    assert "model-a" in validated.errors
