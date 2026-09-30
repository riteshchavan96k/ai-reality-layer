import importlib
from unittest.mock import Mock

import pytest

from backend.app.execution.execution_budget import ExecutionBudget
from backend.app.orchestrator.stage_contract import OrchestrationStageContext
from backend.app.orchestrator.state import OrchestrationState


def test_orchestration_stage_contract_is_importable_from_pipeline():
    pipeline_module = importlib.import_module("backend.app.orchestrator.pipeline")
    assert pipeline_module.OrchestrationStageContext is OrchestrationStageContext


def test_stage_context_preserves_shared_state_trace_and_budget():
    state = OrchestrationState(task="step 168 integrity check")
    trace = Mock()
    budget = ExecutionBudget(max_attempts=3)

    context = OrchestrationStageContext(
        state=state,
        trace=trace,
        execution_budget=budget,
    )

    assert context.state is state
    assert context.trace is trace
    assert context.require_budget() is budget


def test_stage_context_budget_can_be_replaced_without_replacing_state():
    state = OrchestrationState(task="step 168 budget check")
    context = OrchestrationStageContext(state=state, trace=Mock())

    first_budget = ExecutionBudget(max_attempts=2)
    second_budget = ExecutionBudget(max_attempts=4)

    context.set_budget(first_budget)
    assert context.require_budget() is first_budget

    context.set_budget(second_budget)
    assert context.require_budget() is second_budget
    assert context.state is state


def test_stage_context_requires_budget_before_budgeted_stage():
    context = OrchestrationStageContext(
        state=OrchestrationState(task="step 168 missing budget check"),
        trace=Mock(),
    )

    with pytest.raises(RuntimeError, match="execution budget is not available"):
        context.require_budget()
