from unittest.mock import Mock

import pytest

from backend.app.evaluation.quality_recovery import recover_with_evaluation
from backend.app.evaluation.response_evaluation_contract import (
    ResponseEvaluationResult,
)
from backend.app.evaluation.response_evaluation_normalizer import (
    ResponseEvaluationResultNormalizer,
)
from backend.app.evaluation.response_evaluator import evaluate_response
from backend.app.execution.execution_budget import ExecutionBudget
from backend.app.execution.retry_policy import RetryPolicy
from backend.app.orchestrator.pipeline import OrchestrationPipeline
from backend.app.orchestrator.stage_contract import OrchestrationStageContext
from backend.app.orchestrator.state import OrchestrationState


def _canonical_execution():
    return {
        "status": "success",
        "model": "model-a",
        "attempts": 1,
        "total_attempts": 1,
        "budget_limit": 2,
        "attempts_by_model": {"model-a": 1},
        "fallback_used": False,
        "result": {
            "text": "answer",
            "model": "model-a",
            "provider": "test-provider",
        },
        "errors": None,
    }


def test_minimal_evaluation_mapping_is_canonical_and_preserved():
    result = ResponseEvaluationResultNormalizer.normalize(
        {
            "score": 0.75,
            "status": "review",
            "custom_signal": {"name": "prototype"},
        }
    )

    assert isinstance(result, ResponseEvaluationResult)
    assert result.score == 0.75
    assert result.status == "review"
    assert result.to_dict()["custom_signal"] == {"name": "prototype"}


@pytest.mark.parametrize(
    "score",
    [-0.01, 1.01, True, float("nan"), float("inf")],
)
def test_invalid_evaluation_scores_are_rejected(score):
    with pytest.raises(ValueError, match="score must be a finite number between 0 and 1"):
        ResponseEvaluationResultNormalizer.normalize(
            {"score": score, "status": "review"}
        )


def test_invalid_evaluation_status_is_rejected():
    with pytest.raises(ValueError, match="status must be 'pass' or 'review'"):
        ResponseEvaluationResult.validate(
            {"score": 0.5, "status": "unknown"}
        )


def test_structural_evaluation_metadata_is_validated():
    with pytest.raises(ValueError, match="passed_checks cannot exceed total_checks"):
        ResponseEvaluationResultNormalizer.normalize(
            {
                "score": 0.5,
                "status": "review",
                "checks": {"non_empty_response": True},
                "passed_checks": 2,
                "total_checks": 1,
                "structural_score": 0.5,
            }
        )


def test_response_evaluator_returns_canonical_compatible_shape():
    evaluation = evaluate_response(
        "Explain Python recursion",
        {
            "text": "Python recursion uses recursive Python function calls.",
            "model": "model-a",
            "provider": "test-provider",
        },
        {"task_type": "programming"},
        {"model": "model-a"},
    )

    normalized = ResponseEvaluationResultNormalizer.normalize(evaluation)

    assert normalized.to_dict() == evaluation
    assert evaluation["status"] == "pass"
    assert 0.0 <= evaluation["score"] <= 1.0
    assert evaluation["task"] == "Explain Python recursion"
    assert isinstance(evaluation["checks"], dict)
    assert isinstance(evaluation["relevance"], dict)


def test_quality_recovery_preserves_legacy_minimal_evaluation_callers():
    initial_execution = _canonical_execution()
    budget = ExecutionBudget(max_attempts=1, used_attempts=1)

    result = recover_with_evaluation(
        task="test task",
        candidates=["model-a"],
        adapter_resolver=lambda _: None,
        analysis={"task_type": "general"},
        routing={"model": "model-a"},
        initial_execution=initial_execution,
        initial_evaluation={"score": 0.4, "status": "review"},
        retry_policy=RetryPolicy(max_attempts=1),
        execution_budget=budget,
    )

    assert result["improved"] is False
    assert result["best"]["evaluation"] == {
        "score": 0.4,
        "status": "review",
    }


def _pipeline_context():
    state = OrchestrationState(task="test task")
    state.analysis = {"task_type": "general"}
    state.routing = {
        "model": "model-a",
        "candidates": ["model-a"],
    }
    state.execution_context = {}
    state.execution = _canonical_execution()

    trace = Mock()
    return OrchestrationStageContext(
        state=state,
        trace=trace,
        execution_budget=ExecutionBudget(max_attempts=2, used_attempts=1),
    )


def test_pipeline_rejects_malformed_injected_evaluator_before_recovery():
    recover = Mock()
    pipeline = OrchestrationPipeline(
        dependencies=Mock(),
        analyze=Mock(),
        route=Mock(),
        evaluate=Mock(return_value={"score": 1.5, "status": "pass"}),
        recover=recover,
        fallback=Mock(),
    )
    context = _pipeline_context()

    with pytest.raises(ValueError, match="score must be a finite number between 0 and 1"):
        pipeline._evaluate_and_recover(
            context,
            RetryPolicy(max_attempts=1),
        )

    recover.assert_not_called()


def test_pipeline_validates_nested_recovery_evaluation():
    context = _pipeline_context()
    initial_execution = context.state.execution

    recover = Mock(
        return_value={
            "used": False,
            "reason": "test",
            "improved": False,
            "best": {
                "model": "model-a",
                "execution": initial_execution,
                "evaluation": {
                    "score": 2.0,
                    "status": "pass",
                },
            },
            "recovery_attempts": 0,
            "candidates_tried": [],
        }
    )
    pipeline = OrchestrationPipeline(
        dependencies=Mock(),
        analyze=Mock(),
        route=Mock(),
        evaluate=Mock(
            return_value={
                "score": 0.4,
                "status": "review",
                "custom_signal": "initial",
            }
        ),
        recover=recover,
        fallback=Mock(),
    )

    with pytest.raises(ValueError, match="score must be a finite number between 0 and 1"):
        pipeline._evaluate_and_recover(
            context,
            RetryPolicy(max_attempts=1),
        )


def test_pipeline_preserves_valid_evaluation_metadata():
    context = _pipeline_context()
    initial_execution = context.state.execution

    recover = Mock(
        return_value={
            "used": False,
            "reason": "test",
            "improved": False,
            "best": {
                "model": "model-a",
                "execution": initial_execution,
                "evaluation": {
                    "score": 0.4,
                    "status": "review",
                    "custom_signal": {"source": "recovery"},
                },
            },
            "recovery_attempts": 0,
            "candidates_tried": [],
        }
    )
    pipeline = OrchestrationPipeline(
        dependencies=Mock(),
        analyze=Mock(),
        route=Mock(),
        evaluate=Mock(
            return_value={
                "score": 0.4,
                "status": "review",
                "custom_signal": {"source": "initial"},
            }
        ),
        recover=recover,
        fallback=Mock(),
    )

    pipeline._evaluate_and_recover(
        context,
        RetryPolicy(max_attempts=1),
    )

    assert context.state.evaluation["custom_signal"] == {
        "source": "initial"
    }
    assert context.state.recovery["best"]["evaluation"]["custom_signal"] == {
        "source": "recovery"
    }
