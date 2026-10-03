import hashlib
from unittest.mock import Mock

from backend.app.evaluation.quality_recovery import recover_with_evaluation
from backend.app.execution.execution_budget import ExecutionBudget
from backend.app.execution.model_execution_normalizer import ModelExecutionResultNormalizer
from backend.app.execution.retry_policy import RetryPolicy
from backend.app.orchestrator.dependencies import OrchestrationDependencies
from backend.app.orchestrator.pipeline import OrchestrationPipeline
from backend.app.orchestrator.stage_contract import OrchestrationStageContext
from backend.app.orchestrator.state import OrchestrationState


def _initial_execution():
    return {
        "status": "success",
        "model": "initial-model",
        "attempts": 1,
        "total_attempts": 1,
        "budget_limit": 4,
        "attempts_by_model": {"initial-model": 1},
        "fallback_used": False,
        "result": {
            "text": "unrelated response",
            "model": "initial-model",
            "provider": "provider-a",
        },
        "errors": None,
    }


def _review_evaluation():
    return {"status": "review", "score": 0.2}


def _recover_with_provider():
    calls = []

    def provider_executor(provider, model, task, context):
        calls.append((provider, model, task, context))
        if len(calls) == 1:
            return {
                "status": "failed",
                "execution_performed": True,
                "reason": "transient_provider_failure",
            }
        return {
            "status": "completed",
            "execution_performed": True,
            "result": {
                "text": "Python recursion explains recursive Python calls.",
                "model": model,
                "provider": provider,
            },
        }

    budget = ExecutionBudget(max_attempts=4, used_attempts=1)
    recovery = recover_with_evaluation(
        task="Explain Python recursion",
        candidates=["initial-model", "recovery-model"],
        adapter_resolver=lambda _: None,
        analysis={"task_type": "programming"},
        routing={"model": "initial-model"},
        initial_execution=_initial_execution(),
        initial_evaluation=_review_evaluation(),
        retry_policy=RetryPolicy(max_attempts=2),
        execution_budget=budget,
        context={"status": "ready"},
        provider_name_resolver=lambda _: "provider-b",
        invocation_executor=provider_executor,
    )
    return recovery, budget, calls


def test_provider_recovery_returns_canonical_execution_outcome():
    recovery, budget, calls = _recover_with_provider()

    assert recovery["improved"] is True
    assert recovery["best"]["model"] == "recovery-model"
    assert len(calls) == 2
    assert budget.used_attempts == 3

    execution = ModelExecutionResultNormalizer.normalize(
        recovery["best"]["execution"]
    )

    assert execution.status == "success"
    assert execution.model == "recovery-model"
    assert execution.attempts == 2
    assert execution.total_attempts == 3
    assert execution.attempts_by_model == {
        "initial-model": 1,
        "recovery-model": 2,
    }
    assert execution.fallback_used is True


class _RecoveryAdapter:
    def generate(self, task, context=None):
        return {
            "text": "Python recursion explains recursive Python calls.",
            "model": "recovery-model",
            "provider": "legacy-provider",
        }


def test_legacy_adapter_recovery_returns_canonical_execution_outcome():
    budget = ExecutionBudget(max_attempts=3, used_attempts=1)
    recovery = recover_with_evaluation(
        task="Explain Python recursion",
        candidates=["initial-model", "recovery-model"],
        adapter_resolver=lambda name: _RecoveryAdapter()
        if name == "recovery-model"
        else None,
        analysis={"task_type": "programming"},
        routing={"model": "initial-model"},
        initial_execution=_initial_execution(),
        initial_evaluation=_review_evaluation(),
        retry_policy=RetryPolicy(max_attempts=1),
        execution_budget=budget,
    )

    execution = ModelExecutionResultNormalizer.normalize(
        recovery["best"]["execution"]
    )

    assert recovery["improved"] is True
    assert execution.total_attempts == 2
    assert execution.attempts_by_model == {
        "initial-model": 1,
        "recovery-model": 1,
    }
    assert execution.fallback_used is True


def test_recovered_execution_fits_pipeline_success_contract():
    recovery, _, _ = _recover_with_provider()
    recovered_execution = recovery["best"]["execution"]

    state = OrchestrationState(task="Explain Python recursion")
    state.analysis = {"task_type": "programming"}
    state.routing = {
        "model": "initial-model",
        "candidates": ["initial-model", "recovery-model"],
    }
    state.approval = {"required": False}
    state.execution = recovered_execution
    state.evaluation = recovery["best"]["evaluation"]
    state.recovery = recovery
    state.outcome = {
        "record_id": 1,
        "task_fingerprint": hashlib.sha256(
            state.task.encode("utf-8")
        ).hexdigest(),
        "task_type": "programming",
        "routed_model": "initial-model",
        "executed_model": recovered_execution["model"],
        "execution_status": recovered_execution["status"],
        "evaluation_score": recovery["best"]["evaluation"]["score"],
        "attempts": recovered_execution["attempts"],
        "total_attempts": recovered_execution["total_attempts"],
        "budget_limit": recovered_execution["budget_limit"],
        "fallback_used": recovered_execution["fallback_used"],
        "timestamp": "2026-10-03T00:00:00+00:00",
    }

    trace = Mock()
    trace.snapshot.return_value = []
    context = OrchestrationStageContext(state=state, trace=trace)

    pipeline = OrchestrationPipeline(
        dependencies=Mock(spec=OrchestrationDependencies),
        analyze=Mock(),
        route=Mock(),
        evaluate=Mock(),
        recover=Mock(),
        fallback=Mock(),
    )

    result = pipeline._success_result(
        context,
        grounding_result={
            "status": "not_available",
            "grounded": False,
            "source_count": 0,
            "sources": [],
        },
    )

    assert result["status"] == "orchestrated"
    assert result["execution"]["model"] == "recovery-model"
    assert result["execution"]["attempts_by_model"] == {
        "initial-model": 1,
        "recovery-model": 2,
    }
    assert result["execution"]["fallback_used"] is True
