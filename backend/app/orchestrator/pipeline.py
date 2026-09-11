from typing import Any, Callable

from backend.app.execution.execution_budget import ExecutionBudget
from backend.app.execution.execution_trace import ExecutionTrace
from backend.app.execution.outcome_memory import OutcomeMemory
from backend.app.execution.persistent_outcome_memory import PersistentOutcomeMemory
from backend.app.execution.retry_policy import RetryPolicy
from backend.app.models.registry import get_model_adapter, get_model_provider_name
from backend.app.orchestrator.dependencies import OrchestrationDependencies


class OrchestrationPipeline:
    """Execute the AI Reality Layer pipeline through explicit stage boundaries."""

    def __init__(
        self,
        dependencies: OrchestrationDependencies,
        analyze: Callable[[str], dict],
        route: Callable[..., dict],
        evaluate: Callable[..., dict],
        recover: Callable[..., dict],
        fallback: Callable[..., dict],
    ) -> None:
        self.dependencies = dependencies
        self.analyze = analyze
        self.route = route
        self.evaluate = evaluate
        self.recover = recover
        self.fallback = fallback

    def run(
        self,
        task: str,
        human_approved: bool,
        approval_policy: Any | None,
        retry_policy: RetryPolicy,
        execution_budget: ExecutionBudget | None,
        outcome_memory: OutcomeMemory | PersistentOutcomeMemory,
        retrieval_engine: Any | None,
    ) -> dict:
        trace = ExecutionTrace()
        analysis, routing, approval = self._prepare_and_approve(
            task, human_approved, approval_policy, outcome_memory, trace
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

        reality_retrieval, normalized_evidence, evidence_quality, grounding_context = (
            self._retrieve_and_ground(task, analysis, retrieval_engine)
        )
        retrieval_contract = analysis["reality_retrieval"]

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
                "grounding": self.dependencies.grounded_result_builder.build(
                    grounding_context, None
                ),
                "trace": trace.snapshot(),
            }

        execution, budget = self._execute(
            task, routing, retry_policy, execution_budget, grounding_context, trace
        )

        if execution["status"] == "failed":
            outcome = outcome_memory.record(task, analysis, routing, execution, None)
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

        execution, evaluation, recovery = self._evaluate_and_recover(
            task, analysis, routing, execution, retry_policy, budget, grounding_context, trace
        )
        result = execution["result"]
        grounding_result = self.dependencies.grounded_result_builder.build(
            grounding_context, result
        )
        outcome = outcome_memory.record(task, analysis, routing, execution, evaluation)

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

    def _prepare_and_approve(
        self,
        task: str,
        human_approved: bool,
        approval_policy: Any | None,
        outcome_memory: OutcomeMemory | PersistentOutcomeMemory,
        trace: ExecutionTrace,
    ) -> tuple[dict, dict, dict]:
        reality_context = self.dependencies.context_detector.detect(task)
        reality_source_plan = self.dependencies.source_planner.plan(reality_context)
        retrieval_contract = self.dependencies.retrieval_contract.build(task, reality_source_plan)
        analysis = {
            **self.analyze(task),
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

        routing = self.route(task, analysis["task_type"], outcome_memory=outcome_memory)
        trace.record(
            "routing",
            "completed",
            strategy=routing["strategy"],
            model=routing["model"],
            candidate_count=len(routing["candidates"]),
            optimization_status=routing["optimization"]["status"],
            exploration=routing["optimization"]["exploration"],
        )

        policy = approval_policy or self.dependencies.approval_policy
        approval = policy.evaluate(task, analysis, routing)
        trace.record(
            "approval",
            "required" if approval["required"] else "not_required",
            risk_level=approval["risk_level"],
            mode=approval["mode"],
        )
        return analysis, routing, approval

    def _retrieve_and_ground(
        self,
        task: str,
        analysis: dict,
        retrieval_engine: Any | None,
    ) -> tuple[dict, dict, dict, dict]:
        retrieval_service = retrieval_engine or self.dependencies.retrieval_engine
        retrieval_contract = analysis["reality_retrieval"]
        reality_retrieval = retrieval_service.retrieve(retrieval_contract)
        normalized_evidence = self.dependencies.evidence_normalizer.normalize(reality_retrieval)
        evidence_quality = self.dependencies.evidence_quality_validator.validate(normalized_evidence)
        grounding_context = self.dependencies.grounding_context_builder.build(
            task, normalized_evidence
        )
        analysis["reality_retrieval"] = {
            **retrieval_contract,
            "execution": reality_retrieval,
            "evidence": normalized_evidence,
            "quality": evidence_quality,
            "grounding": grounding_context,
        }
        return reality_retrieval, normalized_evidence, evidence_quality, grounding_context

    def _execute(
        self,
        task: str,
        routing: dict,
        retry_policy: RetryPolicy,
        execution_budget: ExecutionBudget | None,
        grounding_context: dict,
        trace: ExecutionTrace,
    ) -> tuple[dict, ExecutionBudget]:
        selected_model = routing["model"]
        fallback_candidates = [
            model for model in routing["candidates"] if model != selected_model
        ]
        candidate_order = (
            [selected_model, *fallback_candidates] if selected_model else fallback_candidates
        )
        budget = execution_budget or ExecutionBudget(
            max_attempts=retry_policy.max_attempts * max(len(candidate_order), 1)
        )
        execution = self.fallback(
            task=task,
            model_names=candidate_order,
            adapter_resolver=get_model_adapter,
            retry_policy=retry_policy,
            execution_budget=budget,
            context=grounding_context,
            provider_name_resolver=get_model_provider_name,
            invocation_executor=self.dependencies.provider_executor.execute,
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
        return execution, budget

    def _evaluate_and_recover(
        self,
        task: str,
        analysis: dict,
        routing: dict,
        execution: dict,
        retry_policy: RetryPolicy,
        execution_budget: ExecutionBudget,
        grounding_context: dict,
        trace: ExecutionTrace,
    ) -> tuple[dict, dict, dict]:
        evaluation = self.evaluate(
            task,
            execution["result"],
            analysis,
            {**routing, "model": execution["model"]},
        )
        trace.record("evaluation", evaluation["status"], score=evaluation["score"])

        candidate_order = (
            [routing["model"], *[model for model in routing["candidates"] if model != routing["model"]]]
            if routing["model"]
            else list(routing["candidates"])
        )
        recovery = self.recover(
            task=task,
            candidates=candidate_order,
            adapter_resolver=get_model_adapter,
            analysis=analysis,
            routing=routing,
            initial_execution=execution,
            initial_evaluation=evaluation,
            retry_policy=retry_policy,
            execution_budget=execution_budget,
            context=grounding_context,
            provider_name_resolver=get_model_provider_name,
            invocation_executor=self.dependencies.provider_executor.execute,
        )

        if recovery["improved"]:
            execution = recovery["best"]["execution"]
            evaluation = recovery["best"]["evaluation"]

        trace.record(
            "quality_recovery",
            "improved" if recovery["improved"] else "not_improved",
            used=recovery["used"],
            recovery_attempts=recovery["recovery_attempts"],
            candidates_tried=recovery["candidates_tried"],
            final_model=recovery["best"]["model"],
            final_score=recovery["best"]["evaluation"]["score"],
        )
        return execution, evaluation, recovery
