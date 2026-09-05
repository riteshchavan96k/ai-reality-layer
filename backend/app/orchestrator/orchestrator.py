from backend.app.analyzer.task_analyzer import analyze_task
from backend.app.router.model_router import route_task
from backend.app.models.registry import get_model_adapter
from backend.app.controls.human_in_the_loop import HumanApprovalPolicy


def orchestrate_task(
    task: str,
    human_approved: bool = False,
    approval_policy: HumanApprovalPolicy | None = None,
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

    model = get_model_adapter(routing["model"])

    if model is None:
        return {
            "status": "error",
            "message": "Model not available",
        }

    result = model.generate(task)

    return {
        "status": "orchestrated",
        "analysis": analysis,
        "routing": routing,
        "approval": approval,
        "result": result,
    }
