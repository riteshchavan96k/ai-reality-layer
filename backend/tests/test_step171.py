from unittest.mock import Mock

import pytest

from backend.app.evaluation.quality_recovery import recover_with_evaluation
from backend.app.evaluation.quality_recovery_contract import (
    QualityRecoveryResult,
)
from backend.app.evaluation.quality_recovery_normalizer import (
    QualityRecoveryResultNormalizer,
)
from backend.app.execution.execution_budget import ExecutionBudget
from backend.app.execution.retry_policy import RetryPolicy
from backend.app.orchestrator.pipeline import OrchestrationPipeline
from backend.app.orchestrator.stage_contract import OrchestrationStageContext
from backend.app.orchestrator.state import OrchestrationState


def _minimal_execution(model="model-a"):
    return {
        "status": "success",
        "model": model,
        "result": {
            "text": "answer",
            "model": model,
            "provider": "test-provider",
        },
    }


def _canonical_execution(model="model-a", total_attempts=1, budget_limit=3):
    return {
        "status": "success",
        "model": model,
        "attempts": 1,
        "total_attempts": total_attempts,
        "budget_limit": budget_limit,
        "attempts_by_model": {model: total_attempts},
        "fallback_used": False,
        "result": {
            "text": "answer",
            "model": model,
            "provider": "test-provider",
        },
        "errors": None,
    }


def _valid_envelope(**overrides):
    value = {
        "used": False,
        "reason": "initial_evaluation_passed",
        "improved": False,
        "best": {
            "model": "model-a",
            "execution": _minimal_execution("model-a"),
            "evaluation": {
                "score": 0.9,
                "status": "pass",
            },
        },
        "recovery_attempts": 0,
        "candidates_tried": [],
    }
    value.update(overrides)
    return value


def test_recovery_envelope_accepts_valid_mapping_and_preserves_extensions():
    raw = _valid_envelope(custom_signal={"source": "step171"})

    result = QualityRecoveryResultNormalizer.normalize(raw)

    assert isinstance(result, QualityRecoveryResult)
    assert result.best.model == "model-a"
    assert result.best.evaluation.score == 0.9
    assert result.to_dict()["custom_signal"] == {"source": "step171"}


def test_used_must_match_candidates_tried():
    with pytest.raises(
        ValueError,
        match="used must match whether candidates_tried is non-empty",
    ):
        QualityRecoveryResultNormalizer.normalize(
            _valid_envelope(
                used=False,
                recovery_attempts=1,
                candidates_tried=["model-b"],
            )
        )


def test_used_recovery_requires_positive_attempt_count():
    with pytest.raises(
        ValueError,
        match="used recovery must report at least one recovery attempt",
    ):
        QualityRecoveryResultNormalizer.normalize(
            _valid_envelope(
                used=True,
                recovery_attempts=0,
                candidates_tried=["model-b"],
            )
        )


def test_improved_best_model_must_have_been_tried():
    with pytest.raises(
        ValueError,
        match="improved best model must appear in candidates_tried",
    ):
        QualityRecoveryResultNormalizer.normalize(
            _valid_envelope(
                used=True,
                improved=True,
                recovery_attempts=1,
                candidates_tried=["model-b"],
                best={
                    "model": "model-c",
                    "execution": _minimal_execution("model-c"),
                    "evaluation": {
                        "score": 1.0,
                        "status": "pass",
                    },
                },
            )
        )


def test_best_execution_model_must_match_best_model():
    with pytest.raises(
        ValueError,
        match="best execution model must match",
    ):
        QualityRecoveryResultNormalizer.normalize(
            _valid_envelope(
                best={
                    "model": "model-a",
                    "execution": _minimal_execution("model-b"),
                    "evaluation": {
                        "score": 0.9,
                        "status": "pass",
                    },
                }
            )
        )


def test_nested_evaluation_is_canonical():
    with pytest.raises(
        ValueError,
        match="score must be a finite number between 0 and 1",
    ):
        QualityRecoveryResultNormalizer.normalize(
            _valid_envelope(
                best={
                    "model": "model-a",
                    "execution": _minimal_execution("model-a"),
                    "evaluation": {
                        "score": 2.0,
                        "status": "pass",
                    },
                }
            )
        )


def test_builtin_pass_path_returns_canonical_recovery_envelope():
    initial_execution = _minimal_execution("model-a")
    result = recover_with_evaluation(
        task="Explain AI",
        candidates=["model-a", "model-b"],
        adapter_resolver=lambda _: None,
        analysis={"task_type": "general"},
        routing={"model": "model-a"},
        initial_execution=initial_execution,
        initial_evaluation={"score": 0.9, "status": "pass"},
        retry_policy=RetryPolicy(max_attempts=1),
        execution_budget=ExecutionBudget(max_attempts=2),
    )

    normalized = QualityRecoveryResultNormalizer.normalize(result)

    assert normalized.used is False
    assert normalized.improved is False
    assert normalized.recovery_attempts == 0
    assert normalized.best.model == "model-a"


def test_builtin_failed_provider_preserves_legacy_direct_caller_shape():
    calls = []

    def provider_executor(provider, model, task, context):
        calls.append(model)
        return {
            "status": "failed",
            "execution_performed": True,
            "reason": "provider_execution_failed",
        }

    result = recover_with_evaluation(
        task="Explain AI",
        candidates=["initial-model", "recovery-model"],
        adapter_resolver=lambda _: None,
        analysis={"task_type": "general"},
        routing={"model": "initial-model"},
        initial_execution=_minimal_execution("initial-model"),
        initial_evaluation={"score": 0.4, "status": "review"},
        retry_policy=RetryPolicy(max_attempts=1),
        execution_budget=ExecutionBudget(max_attempts=1),
        provider_name_resolver=lambda _: "provider-b",
        invocation_executor=provider_executor,
    )

    normalized = QualityRecoveryResultNormalizer.normalize(result)

    assert calls == ["recovery-model"]
    assert normalized.used is True
    assert normalized.improved is False
    assert normalized.recovery_attempts == 1
    assert normalized.candidates_tried == ("recovery-model",)
    assert normalized.best.model == "initial-model"


def _pipeline_context():
    state = OrchestrationState(task="test task")
    state.analysis = {"task_type": "general"}
    state.routing = {
        "model": "model-a",
        "candidates": ["model-a", "model-b"],
    }
    state.execution_context = {}
    state.execution = _canonical_execution("model-a")

    trace = Mock()
    return OrchestrationStageContext(
        state=state,
        trace=trace,
        execution_budget=ExecutionBudget(
            max_attempts=3,
            used_attempts=1,
        ),
    )


def _pipeline(recover):
    return OrchestrationPipeline(
        dependencies=Mock(),
        analyze=Mock(),
        route=Mock(),
        evaluate=Mock(
            return_value={
                "score": 0.4,
                "status": "review",
            }
        ),
        recover=recover,
        fallback=Mock(),
    )


def test_pipeline_rejects_malformed_recovery_envelope_before_consumption():
    context = _pipeline_context()
    recover = Mock(
        return_value={
            "used": False,
            "reason": "test",
            "improved": False,
            "best": {
                "model": "model-a",
                "execution": context.state.execution,
                "evaluation": {
                    "score": 0.4,
                    "status": "review",
                },
            },
            "recovery_attempts": 0,
        }
    )

    with pytest.raises(
        ValueError,
        match="quality recovery result missing fields: candidates_tried",
    ):
        _pipeline(recover)._evaluate_and_recover(
            context,
            RetryPolicy(max_attempts=1),
        )


def test_pipeline_rejects_recovery_attempt_count_that_disagrees_with_budget():
    context = _pipeline_context()
    recover = Mock(
        return_value={
            "used": True,
            "reason": "test",
            "improved": True,
            "best": {
                "model": "model-b",
                "execution": _canonical_execution(
                    "model-b",
                    total_attempts=2,
                    budget_limit=3,
                ),
                "evaluation": {
                    "score": 0.9,
                    "status": "pass",
                },
            },
            "recovery_attempts": 1,
            "candidates_tried": ["model-b"],
        }
    )

    with pytest.raises(
        ValueError,
        match="recovery_attempts must match shared execution budget consumption",
    ):
        _pipeline(recover)._evaluate_and_recover(
            context,
            RetryPolicy(max_attempts=1),
        )


def test_pipeline_rejects_improved_flag_that_does_not_match_model_replacement():
    context = _pipeline_context()
    recover = Mock(
        return_value={
            "used": False,
            "reason": "test",
            "improved": False,
            "best": {
                "model": "model-b",
                "execution": _minimal_execution("model-b"),
                "evaluation": {
                    "score": 0.4,
                    "status": "review",
                },
            },
            "recovery_attempts": 0,
            "candidates_tried": [],
        }
    )

    with pytest.raises(
        ValueError,
        match="improved must match whether the best model replaced the initial model",
    ):
        _pipeline(recover)._evaluate_and_recover(
            context,
            RetryPolicy(max_attempts=1),
        )


def test_pipeline_rejects_noncanonical_best_execution():
    context = _pipeline_context()
    recover = Mock(
        return_value={
            "used": False,
            "reason": "test",
            "improved": False,
            "best": {
                "model": "model-a",
                "execution": _minimal_execution("model-a"),
                "evaluation": {
                    "score": 0.4,
                    "status": "review",
                },
            },
            "recovery_attempts": 0,
            "candidates_tried": [],
        }
    )

    with pytest.raises(ValueError, match="missing required fields"):
        _pipeline(recover)._evaluate_and_recover(
            context,
            RetryPolicy(max_attempts=1),
        )


def test_pipeline_accepts_valid_no_recovery_envelope_and_preserves_extensions():
    context = _pipeline_context()
    recover = Mock(
        return_value={
            "used": False,
            "reason": "test",
            "improved": False,
            "best": {
                "model": "model-a",
                "execution": context.state.execution,
                "evaluation": {
                    "score": 0.4,
                    "status": "review",
                    "custom_signal": "validated",
                },
            },
            "recovery_attempts": 0,
            "candidates_tried": [],
            "diagnostic": {"source": "injected-recovery"},
        }
    )

    _pipeline(recover)._evaluate_and_recover(
        context,
        RetryPolicy(max_attempts=1),
    )

    assert context.state.recovery["diagnostic"] == {
        "source": "injected-recovery"
    }
    assert (
        context.state.recovery["best"]["evaluation"]["custom_signal"]
        == "validated"
    )
    assert context.state.execution["model"] == "model-a"
