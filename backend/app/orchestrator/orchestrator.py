from backend.app.analyzer.task_analyzer import analyze_task
from backend.app.router.model_router import route_task
from backend.app.models.registry import get_model_adapter
from backend.app.controls.human_in_the_loop import HumanApprovalPolicy
from backend.app.evaluation.response_evaluator import evaluate_response
from backend.app.execution.retry_policy import RetryPolicy
from backend.app.execution.fallback_executor import execute_with_fallback
from backend.app.execution.execution_trace import ExecutionTrace
from backend.app.execution.execution_budget import ExecutionBudget
from backend.app.execution.outcome_memory import DEFAULT_OUTCOME_MEMORY, OutcomeMemory


def orchestrate_task(
    task: str,
    human_approved: bool = False,
    approval_policy: HumanApprovalPolicy | None = None,
    retry_policy: RetryPolicy | None = None,
    execution_budget: ExecutionBudget | None = None,
    outcome_memory: OutcomeMemory | None = None,
) -> dict:
    trace = ExecutionTrace()

    analysis = analyze_task(task)
    trace.record(
        "analysis",
        "completed",
        task_type=analysis["task_type"],
        confidence=analysis["confidence"],
    )

    routing = route_task(task, analysis["task_type"])
    trace.record(
        "routing",
        "completed",
        strategy=routing["strategy"],
        model=routing["model"],
        candidate_count=len(routing["candidates"]),
    )

    policy = approval_policy or HumanApprovalPolicy()
    approval = policy.evaluate(task, analysis, routing)
    trace.record(
        "approval",
        "required" if approval["required"] else "not_required",
        risk_level=approval["risk_level"],
        mode=approval["mode"],
    )

    if approval["required"] and not human_approved:
        trace.record("execution", "blocked", reason="human_approval_required")
        return {
            "status": "awaiting_human_approval",
            "analysis": analysis,
            "routing": routing,
            "approval": approval,
            "trace": trace.snapshot(),
        }

    memory = outcome_memory or DEFAULT_OUTCOME_MEMORY
    execution_policy = retry_policy or RetryPolicy()
    selected_model = routing["model"]
    fallback_candidates = [
        model for model in routing["candidates"] if model != selected_model
    ]
    candidate_order = [selected_model, *fallback_candidates] if selected_model else fallback_candidates
    budget = execution_budget or ExecutionBudget(
        max_attempts=execution_policy.max_attempts * max(len(candidate_order), 1)
    )

    execution = execute_with_fallback(
        task=task,
        model_names=candidate_order,
        adapter_resolver=get_model_adapter,
        retry_policy=execution_policy,
        execution_budget=budget,
    )

    trace.record(
        "execution",
        execution["status"],
        model=execution.get("model"),
        attempts=execution.get("attempts", 0),
        total_attempts=execution.get("total_attempts", 0),
        budget_limit=execution.get("budget_limit"),
        attempts_by_model=execution.get("attempts_by_model", {}),
        fallback_used=execution.get("fallback_used", False),
    )

    if execution["status"] == "failed":
        outcome = memory.record(
            task,
            analysis,
            routing,
            execution,
            None,
        )
        trace.record("evaluation", "skipped", reason="execution_failed")
        return {
            "status": "execution_failed",
            "analysis": analysis,
            "routing": routing,
            "approval": approval,
            "execution": execution,
            "outcome": outcome,
            "trace": trace.snapshot(),
        }

    result = execution["result"]
    evaluation = evaluate_response(
        task,
        result,
        analysis,
        {**routing, "model": execution["model"]},
    )
    trace.record(
        "evaluation",
        evaluation["status"],
        score=evaluation["score"],
    )

    outcome = memory.record(
        task,
        analysis,
        routing,
        execution,
        evaluation,
    )

    return {
        "status": "orchestrated",
        "analysis": analysis,
        "routing": routing,
        "approval": approval,
        "execution": {
            "status": execution["status"],
            "model": execution["model"],
            "attempts": execution["attempts"],
            "total_attempts": execution["total_attempts"],
            "budget_limit": execution["budget_limit"],
            "attempts_by_model": execution["attempts_by_model"],
            "fallback_used": execution["fallback_used"],
        },
        "result": result,
        "evaluation": evaluation,
        "outcome": outcome,
        "trace": trace.snapshot(),
    }
