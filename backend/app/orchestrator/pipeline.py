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
        if not execution_consumption.usable:
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