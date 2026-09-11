import unittest
from unittest.mock import Mock

from backend.app.execution.execution_budget import ExecutionBudget
from backend.app.execution.retry_policy import RetryPolicy
from backend.app.orchestrator.dependencies import OrchestrationDependencies
from backend.app.orchestrator.pipeline import OrchestrationPipeline


class Step57Tests(unittest.TestCase):
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
            "status": "not_required",
            "sources": [],
            "content": "",
        }
        dependencies.evidence_normalizer.normalize.return_value = {
            "status": "usable",
            "sources": [],
            "content": "",
        }
        dependencies.evidence_quality_validator.validate.return_value = {
            "status": "usable",
            "issues": [],
        }
        dependencies.grounding_context_builder.build.return_value = {
            "status": "not_required",
            "source_count": 0,
            "sources": [],
            "content": "",
        }
        dependencies.grounded_result_builder.build.return_value = {
            "status": "ungrounded",
            "result": {"text": "ok"},
        }
        dependencies.provider_executor.execute = Mock()
        return dependencies

    def test_pipeline_runs_through_explicit_stage_boundaries(self):
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
            "best": {
                "model": "test-model",
                "execution": execution,
                "evaluation": evaluation,
            },
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
        dependencies.context_detector.detect.assert_called_once_with("test task")
        dependencies.source_planner.plan.assert_called_once()
        dependencies.retrieval_contract.build.assert_called_once()
        dependencies.approval_policy.evaluate.assert_called_once()
        dependencies.retrieval_engine.retrieve.assert_called_once()
        dependencies.evidence_normalizer.normalize.assert_called_once()
        dependencies.evidence_quality_validator.validate.assert_called_once()
        dependencies.grounding_context_builder.build.assert_called_once()
        memory.record.assert_called_once()

    def test_execution_and_recovery_receive_same_budget(self):
        dependencies = self._dependencies()
        execution = {
            "status": "success",
            "model": "test-model",
            "attempts": 1,
            "total_attempts": 1,
            "budget_limit": 3,
            "attempts_by_model": {"test-model": 1},
            "fallback_used": False,
            "result": {"text": "ok", "model": "test-model"},
        }
        evaluation = {"status": "acceptable", "score": 1.0}
        seen = {}

        def fallback(**kwargs):
            seen["execution_budget"] = kwargs["execution_budget"]
            return execution

        def recover(**kwargs):
            seen["recovery_budget"] = kwargs["execution_budget"]
            return {
                "improved": False,
                "used": False,
                "recovery_attempts": 0,
                "candidates_tried": [],
                "best": {
                    "model": "test-model",
                    "execution": execution,
                    "evaluation": evaluation,
                },
            }

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
            recover=recover,
            fallback=fallback,
        )
        budget = ExecutionBudget(max_attempts=3)
        memory = Mock()
        memory.record.return_value = {"status": "recorded"}

        pipeline.run(
            task="test task",
            human_approved=True,
            approval_policy=None,
            retry_policy=RetryPolicy(max_attempts=1),
            execution_budget=budget,
            outcome_memory=memory,
            retrieval_engine=None,
        )

        self.assertIs(seen["execution_budget"], budget)
        self.assertIs(seen["recovery_budget"], budget)

    def test_pipeline_can_block_before_retrieval_when_approval_is_required(self):
        dependencies = self._dependencies()
        dependencies.approval_policy.evaluate.return_value = {
            "required": True,
            "risk_level": "high",
            "mode": "risk_based",
        }
        analyze = Mock(return_value={"task_type": "general", "confidence": 0.9})
        route = Mock(return_value={
            "strategy": "general",
            "model": "test-model",
            "candidates": ["test-model"],
            "optimization": {"status": "not_applied", "exploration": False},
        })
        pipeline = OrchestrationPipeline(
            dependencies=dependencies,
            analyze=analyze,
            route=route,
            evaluate=Mock(),
            recover=Mock(),
            fallback=Mock(),
        )
        memory = Mock()

        result = pipeline.run(
            task="test task",
            human_approved=False,
            approval_policy=None,
            retry_policy=RetryPolicy(max_attempts=1),
            execution_budget=None,
            outcome_memory=memory,
            retrieval_engine=None,
        )

        self.assertEqual(result["status"], "awaiting_human_approval")
        dependencies.retrieval_engine.retrieve.assert_not_called()
