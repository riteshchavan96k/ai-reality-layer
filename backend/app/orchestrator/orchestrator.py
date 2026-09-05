from backend.app.analyzer.task_analyzer import analyze_task
from backend.app.router.model_router import route_task
from backend.app.models.registry import get_model_adapter
from backend.app.controls.human_in_the_loop import HumanApprovalPolicy
from backend.app.evaluation.response_evaluator import evaluate_response
from backend.app.execution.retry_policy import RetryPolicy
from backend.app.execution.fallback_executor import execute_with_fallback


def orchestrate_task(
    task: str,
    human_approved: bool = False,
    approval_policy: HumanApprovalPolicy | None = None,
    retry_policy: RetryPolicy | None = None,
) -> dict:
    analysis = analyze_task(task)
    routing = route_task(task, analysis["task_type"])

    policy = approval_policy or HumanApprovalPolicy()
    approval = policy.evaluate(task, analysis, routing)

    if approval["required"] and not human_approved:
        return {
            "status": "awaiting_human_approval",
            "analysis": analysis,
            "routing": routing,
            "approval": approval,
        }

    execution_policy = retry_policy or RetryPolicy()
    execution = execute_with_fallback(
        task=task,
        model_names=routing["candidates"],
        adapter_resolver=get_model_adapter,
        retry_policy=execution_policy,
    )

    if execution["status"] == "failed":
        return {
            "status": "execution_failed",
            "analysis": analysis,
            "routing": routing,
            "approval": approval,
            "execution": execution,
        }

    result = execution["result"]
    evaluation = evaluate_response(
        task,
        result,
        analysis,
        {**routing, "model": execution["model"]},
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
            "attempts_by_model": execution["attempts_by_model"],
            "fallback_used": execution["fallback_used"],
        },
        "result": result,
        "evaluation": evaluation,
    }
