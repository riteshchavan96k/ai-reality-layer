import os

from backend.app.analyzer.task_analyzer import analyze_task
from backend.app.router.model_router import route_task
from backend.app.models.registry import get_model_adapter, get_model_provider_name
from backend.app.models.provider_invocation_executor import ProviderInvocationExecutor
from backend.app.controls.human_in_the_loop import HumanApprovalPolicy
from backend.app.evaluation.response_evaluator import evaluate_response
from backend.app.evaluation.quality_recovery import recover_with_evaluation
from backend.app.execution.retry_policy import RetryPolicy
from backend.app.execution.fallback_executor import execute_with_fallback
from backend.app.execution.execution_trace import ExecutionTrace
from backend.app.execution.execution_budget import ExecutionBudget
from backend.app.execution.outcome_memory import DEFAULT_OUTCOME_MEMORY, OutcomeMemory
from backend.app.execution.persistent_outcome_memory import PersistentOutcomeMemory
from backend.app.reality.context_requirements import RealityContextRequirementDetector
from backend.app.reality.source_planner import RealitySourcePlanner
from backend.app.reality.retrieval_contract import RealityRetrievalContract
from backend.app.reality.retrieval_engine import RealityRetrievalEngine
from backend.app.reality.evidence_normalizer import RetrievalEvidenceNormalizer
from backend.app.reality.evidence_quality import EvidenceQualityValidator
from backend.app.reality.grounding_context import EvidenceGroundingContextBuilder
from backend.app.reality.grounded_result import GroundedResultEnvelopeBuilder


DEFAULT_PERSISTENT_MEMORY_PATH = os.getenv(
    "ARL_OUTCOME_MEMORY_PATH",
    "",
)

if DEFAULT_PERSISTENT_MEMORY_PATH:
    DEFAULT_CONFIGURED_MEMORY = PersistentOutcomeMemory(DEFAULT_PERSISTENT_MEMORY_PATH)
else:
    DEFAULT_CONFIGURED_MEMORY = DEFAULT_OUTCOME_MEMORY


def orchestrate_task(
    task: str,
    human_approved: bool = False,
    approval_policy: HumanApprovalPolicy | None = None,
    retry_policy: RetryPolicy | None = None,
    execution_budget: ExecutionBudget | None = None,
    outcome_memory: OutcomeMemory | PersistentOutcomeMemory | None = None,
    retrieval_engine: RealityRetrievalEngine | None = None,
) -> dict:
    trace = ExecutionTrace()
    memory = outcome_memory or DEFAULT_CONFIGURED_MEMORY

    reality_context = RealityContextRequirementDetector().detect(task)
    reality_source_plan = RealitySourcePlanner().plan(reality_context)
    retrieval_contract = RealityRetrievalContract().build(task, reality_source_plan)
    analysis = {
        **analyze_task(task),
        "reality_context": reality_context,
        "reality_source_plan": reality_source_plan,
        "reality_retrieval": retrieval_contract,
    }
    trace.record(
        "analysis",
        "completed",
        task_type=analysis["task_type"],
        confidence=analysis["confidence"],
        needs_current_info=reality_context["needs_current_info"],
        needs_external_evidence=reality_context["needs_external_evidence"],
        source_type=reality_source_plan["source_type"],
        retrieval_required=reality_source_plan["requires_retrieval"],
        retrieval_status=retrieval_contract["status"],
    )

    routing = route_task(
        task,
        analysis["task_type"],
        outcome_memory=memory,
    )
    trace.record(
        "routing",
        "completed",
        strategy=routing["strategy"],
        model=routing["model"],
        candidate_count=len(routing["candidates"]),
        optimization_status=routing["optimization"]["status"],
        exploration=routing["optimization"]["exploration"],
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

    reality_retrieval = (retrieval_engine or RealityRetrievalEngine()).retrieve(
        retrieval_contract
    )
    normalized_evidence = RetrievalEvidenceNormalizer().normalize(reality_retrieval)
    evidence_quality = EvidenceQualityValidator().validate(normalized_evidence)
    grounding_context = EvidenceGroundingContextBuilder().build(
        task,
        normalized_evidence,
    )
    analysis["reality_retrieval"] = {
        **retrieval_contract,
        "execution": reality_retrieval,
        "evidence": normalized_evidence,
        "quality": evidence_quality,
        "grounding": grounding_context,
    }

    if (
        retrieval_contract["request"]["required"]
        and evidence_quality["status"] != "usable"
    ):
        trace.record(
            "execution",
            "blocked",
            reason="required_retrieval_evidence_quality_insufficient",
            retrieval_status=reality_retrieval["status"],
            evidence_status=normalized_evidence["status"],
            quality_status=evidence_quality["status"],
            quality_issues=evidence_quality["issues"],
        )
        return {
            "status": "retrieval_unavailable",
            "analysis": analysis,
            "routing": routing,
            "approval": approval,
            "retrieval": reality_retrieval,
            "evidence": normalized_evidence,
            "evidence_quality": evidence_quality,
            "grounding": GroundedResultEnvelopeBuilder().build(grounding_context, None),
            "trace": trace.snapshot(),
        }

    execution_policy = retry_policy or RetryPolicy()
    selected_model = routing["model"]
    fallback_candidates = [
        model for model in routing["candidates"] if model != selected_model
    ]
    candidate_order = [selected_model, *fallback_candidates] if selected_model else fallback_candidates
    budget = execution_budget or ExecutionBudget(
        max_attempts=execution_policy.max_attempts * max(len(candidate_order), 1)
    )

    provider_executor = ProviderInvocationExecutor()
    execution = execute_with_fallback(
        task=task,
        model_names=candidate_order,
        adapter_resolver=get_model_adapter,
        retry_policy=execution_policy,
        execution_budget=budget,
        context=grounding_context,
        provider_name_resolver=get_model_provider_name,
        invocation_executor=provider_executor.execute,
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
        grounding_status=grounding_context["status"],
        grounding_source_count=grounding_context["source_count"],
    )

    if execution["status"] == "failed":
        outcome = memory.record(task, analysis, routing, execution, None)
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
    trace.record("evaluation", evaluation["status"], score=evaluation["score"])

    recovery = recover_with_evaluation(
        task=task,
        candidates=candidate_order,
        adapter_resolver=get_model_adapter,
        analysis=analysis,
        routing=routing,
        initial_execution=execution,
        initial_evaluation=evaluation,
        retry_policy=execution_policy,
        execution_budget=budget,
        context=grounding_context,
    )

    if recovery["improved"]:
        execution = recovery["best"]["execution"]
        evaluation = recovery["best"]["evaluation"]
        result = execution["result"]

    grounding_result = GroundedResultEnvelopeBuilder().build(
        grounding_context,
        result,
    )

    trace.record(
        "quality_recovery",
        "improved" if recovery["improved"] else "not_improved",
        used=recovery["used"],
        recovery_attempts=recovery["recovery_attempts"],
        candidates_tried=recovery["candidates_tried"],
        final_model=recovery["best"]["model"],
        final_score=recovery["best"]["evaluation"]["score"],
    )

    outcome = memory.record(task, analysis, routing, execution, evaluation)

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
        "grounding": grounding_result,
        "evaluation": evaluation,
        "quality_recovery": recovery,
        "outcome": outcome,
        "trace": trace.snapshot(),
    }
