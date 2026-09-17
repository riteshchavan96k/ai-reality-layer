from typing import Any, Callable

from backend.app.execution.execution_budget import ExecutionBudget
from backend.app.execution.execution_trace import ExecutionTrace
from backend.app.execution.outcome_memory import OutcomeMemory
from backend.app.execution.persistent_outcome_memory import PersistentOutcomeMemory
from backend.app.execution.retry_policy import RetryPolicy
from backend.app.models.registry import get_model_adapter, get_model_provider_name
from backend.app.orchestrator.dependencies import OrchestrationDependencies
from backend.app.orchestrator.stage_contract import OrchestrationStageContext
from backend.app.orchestrator.state import OrchestrationState
from backend.app.reality.grounding_execution_context import GroundingExecutionContext


class OrchestrationPipeline:
    """Execute the AI Reality Layer pipeline through explicit stage boundaries."""

    def __init__(self, dependencies: OrchestrationDependencies, analyze: Callable[[str], dict], route: Callable[..., dict], evaluate: Callable[..., dict], recover: Callable[..., dict], fallback: Callable[..., dict]) -> None:
        self.dependencies = dependencies
        self.analyze = analyze
        self.route = route
        self.evaluate = evaluate
        self.recover = recover
        self.fallback = fallback

    def run(self, task: str, human_approved: bool, approval_policy: Any | None, retry_policy: RetryPolicy, execution_budget: ExecutionBudget | None, outcome_memory: OutcomeMemory | PersistentOutcomeMemory, retrieval_engine: Any | None) -> dict:
        context = OrchestrationStageContext(state=OrchestrationState(task=task), trace=ExecutionTrace(), execution_budget=execution_budget)
        self._prepare_and_approve(context, human_approved, approval_policy, outcome_memory)
        state = context.state
        if state.approval["required"] and not human_approved:
            context.trace.record("execution", "blocked", reason="human_approval_required")
            return self._approval_blocked_result(context)
        self._retrieve_and_ground(context, retrieval_engine)
        state = context.state
        retrieval_contract = state.retrieval_contract
        if retrieval_contract["request"]["required"] and state.evidence_quality["status"] != "usable":
            return self._retrieval_blocked_result(context)
        raw_grounding_consumption = self.dependencies.grounding_context_consumer.consume(state.grounding)
        grounding_consumption = self.dependencies.grounding_context_consumption_normalizer.normalize(raw_grounding_consumption)
        state.analysis["reality_grounding_consumption"] = grounding_consumption.to_dict()
        raw_grounding_gate = self.dependencies.grounding_execution_gate.evaluate(grounding_consumption)
        grounding_gate = self.dependencies.grounding_execution_gate_normalizer.normalize(raw_grounding_gate)
        state.analysis["reality_grounding_execution_gate"] = grounding_gate.to_dict()
        context.trace.record("grounding_gate", grounding_gate.status, allowed=grounding_gate.allowed, reason=grounding_gate.reason, grounding_status=grounding_gate.grounding_status)
        if not grounding_gate.allowed:
            return self._grounding_blocked_result(context)
        raw_execution_context = GroundingExecutionContext.from_grounding(
            state.grounding,
            execution_allowed=grounding_gate.allowed,
        )
        execution_context = self.dependencies.grounding_execution_context_normalizer.normalize(raw_execution_context)
        state.execution_context = execution_context.to_dict()
        state.analysis["reality_grounding_execution_context"] = state.execution_context
        context.trace.record(
            "grounding_execution_context",
            "normalized",
            grounding_status=execution_context.grounding_status,
            source_count=execution_context.source_count,
            execution_allowed=execution_context.execution_allowed,
            context_prepared=execution_context.context_prepared,
        )
        raw_execution_consumption = self.dependencies.grounding_execution_context_consumer.consume(execution_context)
        execution_consumption = self.dependencies.grounding_execution_context_consumption_normalizer.normalize(raw_execution_consumption)
        state.analysis["reality_grounding_execution_context_consumption"] = execution_consumption.to_dict()
        context.trace.record(
            "grounding_execution_context_consumption",
            execution_consumption.status,
            usable=execution_consumption.usable,
            reason=execution_consumption.reason,
            grounding_status=execution_consumption.grounding_status,
        )
        execution_decision = self.dependencies.grounding_execution_context_consumption_decision_evaluator.evaluate(execution_consumption)
        state.analysis["reality_grounding_execution_context_consumption_decision"] = execution_decision.to_dict()
        context.trace.record(
            "grounding_execution_context_consumption_decision",
            execution_decision.status,
            allowed=execution_decision.allowed,
            reason=execution_decision.reason,
            grounding_status=execution_decision.grounding_status,
        )
        execution_authorization = self.dependencies.grounding_execution_authorization_evaluator.evaluate(execution_decision)
        state.analysis["reality_grounding_execution_authorization"] = execution_authorization.to_dict()
        context.trace.record(
            "grounding_execution_authorization",
            execution_authorization.status,
            authorized=execution_authorization.authorized,
            reason=execution_authorization.reason,
            grounding_status=execution_authorization.grounding_status,
        )
        raw_authorization_consumption = self.dependencies.grounding_execution_authorization_consumer.consume(execution_authorization)
        authorization_consumption = self.dependencies.grounding_execution_authorization_consumption_result_normalizer.normalize(raw_authorization_consumption)
        state.analysis["reality_grounding_execution_authorization_consumption"] = authorization_consumption.to_dict()
        context.trace.record(
            "grounding_execution_authorization_consumption",
            authorization_consumption.status,
            usable=authorization_consumption.usable,
            reason=authorization_consumption.reason,
            authorization_status=authorization_consumption.authorization_status,
        )
        raw_authorization_consumption_decision = self.dependencies.grounding_execution_authorization_consumption_decision_evaluator.evaluate(authorization_consumption)
        authorization_consumption_decision = self.dependencies.grounding_execution_authorization_consumption_decision_result_normalizer.normalize(raw_authorization_consumption_decision)
        state.analysis["reality_grounding_execution_authorization_consumption_decision"] = authorization_consumption_decision.to_dict()
        context.trace.record(
            "grounding_execution_authorization_consumption_decision",
            authorization_consumption_decision.status,
            allowed=authorization_consumption_decision.allowed,
            reason=authorization_consumption_decision.reason,
            authorization_status=authorization_consumption_decision.authorization_status,
        )
        if not authorization_consumption_decision.allowed:
            return self._execution_context_blocked_result(context)
        self._execute(context, retry_policy)
        state = context.state
        if state.execution["status"] == "failed":
            state.outcome = outcome_memory.record(task, state.analysis, state.routing, state.execution, None)
            context.trace.record("evaluation", "skipped", reason="execution_failed")
            return self._execution_failed_result(context)
        self._evaluate_and_recover(context, retry_policy)
        state = context.state
        grounding_result = self.dependencies.grounded_result_builder.build(state.grounding, state.result)
        state.outcome = outcome_memory.record(task, state.analysis, state.routing, state.execution, state.evaluation)
        return self._success_result(context, grounding_result)

    def _prepare_and_approve(self, context: OrchestrationStageContext, human_approved: bool, approval_policy: Any | None, outcome_memory: OutcomeMemory | PersistentOutcomeMemory) -> None:
        state = context.state
        reality_context = self.dependencies.context_detector.detect(state.task)
        reality_source_plan = self.dependencies.source_planner.plan(reality_context)
        retrieval_contract = self.dependencies.retrieval_contract.build(state.task, reality_source_plan)
        state.analysis = {**self.analyze(state.task), "reality_context": reality_context, "reality_source_plan": reality_source_plan, "reality_retrieval": retrieval_contract}
        context.trace.record("analysis", "completed", task_type=state.analysis["task_type"], confidence=state.analysis["confidence"], needs_current_info=reality_context["needs_current_info"], needs_external_evidence=reality_context["needs_external_evidence"], source_type=reality_source_plan["source_type"], retrieval_required=reality_source_plan["requires_retrieval"], retrieval_status=retrieval_contract["status"])
        state.routing = self.route(state.task, state.analysis["task_type"], outcome_memory=outcome_memory)
        context.trace.record("routing", "completed", strategy=state.routing["strategy"], model=state.routing["model"], candidate_count=len(state.routing["candidates"]), optimization_status=state.routing["optimization"]["status"], exploration=state.routing["optimization"]["exploration"])
        policy = approval_policy or self.dependencies.approval_policy
        state.approval = policy.evaluate(state.task, state.analysis, state.routing)
        context.trace.record("approval", "required" if state.approval["required"] else "not_required", risk_level=state.approval["risk_level"], mode=state.approval["mode"])

    def _retrieve_and_ground(self, context: OrchestrationStageContext, retrieval_engine: Any | None) -> None:
        state = context.state
        retrieval_service = retrieval_engine or self.dependencies.retrieval_engine
        state.retrieval = retrieval_service.retrieve(state.retrieval_contract)
        raw_consumption = self.dependencies.retrieval_result_consumer.consume(state.retrieval)
        consumption = self.dependencies.retrieval_result_consumption_normalizer.normalize(raw_consumption)
        state.analysis["reality_retrieval_consumption"] = consumption.to_dict()
        if consumption.usable:
            evidence_result = self.dependencies.evidence_normalizer.normalize_result(state.retrieval)
            evidence_consumption = self.dependencies.evidence_normalization_consumer.consume(evidence_result.to_dict())
            state.analysis["reality_evidence_normalization_consumption"] = evidence_consumption.to_dict()
            if evidence_consumption.usable:
                state.evidence = evidence_result.to_dict()
            else:
                state.evidence = {"status": "invalid_evidence", "sources": [], "content": None, "source_count": 0, "has_content": False, "reason": evidence_consumption.reason}
        else:
            state.evidence = {"status": "invalid_evidence", "sources": [], "content": None, "source_count": 0, "has_content": False, "reason": consumption.reason}
        raw_quality_result = self.dependencies.evidence_quality_validator.validate_result(state.evidence)
        quality_result = self.dependencies.evidence_quality_validation_result_normalizer.normalize(raw_quality_result)
        state.evidence_quality = quality_result.to_dict()
        raw_grounding_result = self.dependencies.grounding_context_builder.build_result(state.task, state.evidence)
        grounding_result = self.dependencies.grounding_context_normalizer.normalize(raw_grounding_result)
        state.grounding = grounding_result.to_dict()
        state.analysis["reality_retrieval"] = {**state.retrieval_contract, "execution": state.retrieval, "consumption": consumption.to_dict(), "evidence": state.evidence, "quality": state.evidence_quality, "grounding": state.grounding}

    def _execute(self, context: OrchestrationStageContext, retry_policy: RetryPolicy) -> None:
        state = context.state
        selected_model = state.routing["model"]
        fallback_candidates = [m for m in state.routing["candidates"] if m != selected_model]
        candidate_order = [selected_model, *fallback_candidates] if selected_model else fallback_candidates
        budget = context.execution_budget or ExecutionBudget(max_attempts=retry_policy.max_attempts * max(len(candidate_order), 1))
        context.set_budget(budget)
        state.execution = self.fallback(task=state.task, model_names=candidate_order, adapter_resolver=get_model_adapter, retry_policy=retry_policy, execution_budget=budget, context=state.execution_context, provider_name_resolver=get_model_provider_name, invocation_executor=self.dependencies.provider_executor.execute)
        context.trace.record("execution", state.execution["status"], model=state.execution.get("model"), attempts=state.execution.get("attempts", 0), total_attempts=state.execution.get("total_attempts", 0), budget_limit=state.execution.get("budget_limit"), attempts_by_model=state.execution.get("attempts_by_model", {}), fallback_used=state.execution.get("fallback_used", False), grounding_status=state.execution_context["grounding_status"], grounding_source_count=state.execution_context["source_count"])

    def _evaluate_and_recover(self, context: OrchestrationStageContext, retry_policy: RetryPolicy) -> None:
        state = context.state
        budget = context.require_budget()
        state.evaluation = self.evaluate(state.task, state.result, state.analysis, {**state.routing, "model": state.execution["model"]})
        context.trace.record("evaluation", state.evaluation["status"], score=state.evaluation["score"])
        candidates = ([state.routing["model"], *[m for m in state.routing["candidates"] if m != state.routing["model"]]] if state.routing["model"] else list(state.routing["candidates"]))
        state.recovery = self.recover(task=state.task, candidates=candidates, adapter_resolver=get_model_adapter, analysis=state.analysis, routing=state.routing, initial_execution=state.execution, initial_evaluation=state.evaluation, retry_policy=retry_policy, execution_budget=budget, context=state.execution_context, provider_name_resolver=get_model_provider_name, invocation_executor=self.dependencies.provider_executor.execute)
        if state.recovery["improved"]:
            state.execution = state.recovery["best"]["execution"]
            state.evaluation = state.recovery["best"]["evaluation"]
        context.trace.record("quality_recovery", "improved" if state.recovery["improved"] else "not_improved", used=state.recovery["used"], recovery_attempts=state.recovery["recovery_attempts"], candidates_tried=state.recovery["candidates_tried"], final_model=state.recovery["best"]["model"], final_score=state.recovery["best"]["evaluation"]["score"])

    def _approval_blocked_result(self, context: OrchestrationStageContext) -> dict:
        state = context.state
        return {"status": "awaiting_human_approval", "analysis": state.analysis, "routing": state.routing, "approval": state.approval, "trace": context.trace.snapshot()}

    def _retrieval_blocked_result(self, context: OrchestrationStageContext) -> dict:
        state = context.state
        context.trace.record("execution", "blocked", reason="required_retrieval_evidence_quality_insufficient", retrieval_status=state.retrieval["status"], evidence_status=state.evidence["status"], quality_status=state.evidence_quality["status"], quality_issues=state.evidence_quality["issues"])
        return {"status": "retrieval_unavailable", "analysis": state.analysis, "routing": state.routing, "approval": state.approval, "retrieval": state.retrieval, "evidence": state.evidence, "evidence_quality": state.evidence_quality, "grounding": self.dependencies.grounded_result_builder.build(state.grounding, None), "trace": context.trace.snapshot()}

    def _grounding_blocked_result(self, context: OrchestrationStageContext) -> dict:
        state = context.state
        reason = state.analysis["reality_grounding_execution_gate"].get("reason") or state.analysis["reality_grounding_consumption"].get("reason") or "grounding_context_rejected"
        context.trace.record("execution", "blocked", reason=reason, grounding_status=state.grounding["status"], grounding_source_count=state.grounding["source_count"])
        return {"status": "grounding_unavailable", "analysis": state.analysis, "routing": state.routing, "approval": state.approval, "retrieval": state.retrieval, "evidence": state.evidence, "evidence_quality": state.evidence_quality, "grounding": state.grounding, "trace": context.trace.snapshot()}

    def _execution_context_blocked_result(self, context: OrchestrationStageContext) -> dict:
        state = context.state
        reason = state.analysis["reality_grounding_execution_context_consumption_decision"].get("reason") or state.analysis["reality_grounding_execution_context_consumption"].get("reason") or "execution_context_rejected"
        context.trace.record("execution", "blocked", reason=reason, grounding_status=state.execution_context.get("grounding_status"), grounding_source_count=state.execution_context.get("source_count", 0))
        return {"status": "execution_context_unavailable", "analysis": state.analysis, "routing": state.routing, "approval": state.approval, "retrieval": state.retrieval, "evidence": state.evidence, "evidence_quality": state.evidence_quality, "grounding": state.grounding, "execution_context": state.execution_context, "trace": context.trace.snapshot()}

    def _execution_failed_result(self, context: OrchestrationStageContext) -> dict:
        state = context.state
        return {"status": "execution_failed", "analysis": state.analysis, "routing": state.routing, "approval": state.approval, "execution": state.execution, "outcome": state.outcome, "trace": context.trace.snapshot()}

    def _success_result(self, context: OrchestrationStageContext, grounding_result: dict) -> dict:
        state = context.state
        return {"status": "orchestrated", "analysis": state.analysis, "routing": state.routing, "approval": state.approval, "execution": {"status": state.execution["status"], "model": state.execution["model"], "attempts": state.execution["attempts"], "total_attempts": state.execution["total_attempts"], "budget_limit": state.execution["budget_limit"], "attempts_by_model": state.execution["attempts_by_model"], "fallback_used": state.execution["fallback_used"]}, "result": state.result, "grounding": grounding_result, "evaluation": state.evaluation, "quality_recovery": state.recovery, "outcome": state.outcome, "trace": context.trace.snapshot()}
