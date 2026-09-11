import unittest
from unittest.mock import Mock

from backend.app.execution.execution_budget import ExecutionBudget
from backend.app.execution.retry_policy import RetryPolicy
from backend.app.orchestrator.dependencies import OrchestrationDependencies
from backend.app.orchestrator.pipeline import OrchestrationPipeline
from backend.app.orchestrator.state import OrchestrationState


class Step58Tests(unittest.TestCase):
    def _dependencies(self):
        dependencies = Mock(spec=OrchestrationDependencies)
        dependencies.context_detector.detect.return_value = {
            "needs_current_info": False,
            "needs_external_evidence": False,
        }
        dependencies.source_planner.plan.return_value = {
            "source_type": "model_knowledge",
            "priority": "optional",
            "requires_retrieval": False,
            "temporal_scope": "unspecified",
            "status": "planned",
        }
        dependencies.retrieval_contract.build.return_value = {
            "status": "not_required",
            "request": {"required": False},
        }
        dependencies.approval_policy.evaluate.return_value = {
            "required": False,
            "risk_level": "normal",
            "mode": "test",
        }
        dependencies.retrieval_engine.retrieve.return_value = {
            "status": "not_required", "sources": [], "content": ""
        }
        dependencies.evidence_normalizer.normalize.return_value = {
            "status": "usable", "sources": [], "content": ""
        }
        dependencies.evidence_quality_validator.validate.return_value = {
            "status": "usable", "issues": []
        }
        dependencies.grounding_context_builder.build.return_value = {
            "status": "not_required", "source_count": 0, "sources": [], "content": ""
        }
        dependencies.grounded_result_builder.build.return_value = {
            "status": "ungrounded", "result": {"text": "ok"}
        }
        return dependencies

    def test_state_contract_exposes_named_pipeline_state(self):
        state = OrchestrationState(task="test")
        state.analysis = {"reality_retrieval": {"request": {"required": False}}}
        state.execution = {"result": {"text": "ok"}}

        self.assertEqual(state.task, "test")
        self.assertEqual(state.retrieval_contract["request"]["required"], False)
        self.assertEqual(state.result["text"], "ok")

    def test_pipeline_populates_state_backed_outputs_without_changing_result_shape(self):
        dependencies = self._dependencies()
        execution = {
            "status": "success",
            "model": "test-model",
            "attempts": 1,
            "total_attempts": 1,
            "budget_limit": 2,
            "attempts_by_model": {"test-model": 1},
            "fallback_used": False,
            "result": {"text": "ok", "model": "test-model"},
        }
        evaluation = {"status": "acceptable", "score": 1.0}
        recovery = {
            "improved": False,
            "used": False,
            "recovery_attempts": 0,
            "candidates_tried": [],
            "best": {"model": "test-model", "execution": execution, "evaluation": evaluation},
        }
        memory = Mock()
        memory.record.return_value = {"status": "recorded"}

        pipeline = OrchestrationPipeline(
            dependencies=dependencies,
            analyze=Mock(return_value={"task_type": "general", "confidence": 0.9}),
            route=Mock(return_value={
                "strategy": "general",
                "model": "test-model",
                "candidates": ["test-model"],
                "optimization": {"status": "not_applied", "exploration": False},
            }),
            evaluate=Mock(return_value=evaluation),
            recover=Mock(return_value=recovery),
            fallback=Mock(return_value=execution),
        )

        result = pipeline.run(
            task="test task",
            human_approved=True,
            approval_policy=None,
            retry_policy=RetryPolicy(max_attempts=1),
            execution_budget=ExecutionBudget(max_attempts=2),
            outcome_memory=memory,
            retrieval_engine=None,
        )

        self.assertEqual(result["status"], "orchestrated")
        self.assertEqual(result["result"]["text"], "ok")
        self.assertEqual(result["evaluation"]["score"], 1.0)
        memory.record.assert_called_once()

    def test_state_contract_defaults_keep_optional_stages_empty(self):
        state = OrchestrationState(task="test")
        self.assertEqual(state.analysis, {})
        self.assertEqual(state.execution, {})
        self.assertIsNone(state.result)


if __name__ == "__main__":
    unittest.main()
