import unittest
from dataclasses import replace
from unittest.mock import Mock

from backend.app.execution.execution_budget import ExecutionBudget
from backend.app.execution.outcome_memory import OutcomeMemory
from backend.app.execution.retry_policy import RetryPolicy
from backend.app.orchestrator.dependencies import OrchestrationDependencies
from backend.app.orchestrator.pipeline import OrchestrationPipeline


def _execution(budget_limit):
    return {
        "status": "success",
        "model": "test-model",
        "attempts": 1,
        "total_attempts": 1,
        "budget_limit": budget_limit,
        "attempts_by_model": {"test-model": 1},
        "fallback_used": False,
        "errors": None,
        "result": {
            "text": "ok",
            "model": "test-model",
            "provider": "internal",
        },
    }


def _evaluation():
    return {"status": "pass", "score": 1.0}


def _recovery(execution, evaluation):
    return {
        "improved": False,
        "used": False,
        "reason": "initial_evaluation_passed",
        "recovery_attempts": 0,
        "candidates_tried": [],
        "best": {
            "model": "test-model",
            "execution": execution,
            "evaluation": evaluation,
        },
    }


class Step57Tests(unittest.TestCase):
    def _dependencies(self):
        defaults = OrchestrationDependencies.default()
        return replace(
            defaults,
            context_detector=Mock(wraps=defaults.context_detector),
            source_planner=Mock(wraps=defaults.source_planner),
            retrieval_contract=Mock(wraps=defaults.retrieval_contract),
            approval_policy=Mock(wraps=defaults.approval_policy),
            retrieval_engine=Mock(wraps=defaults.retrieval_engine),
            evidence_normalizer=Mock(wraps=defaults.evidence_normalizer),
            evidence_quality_validator=Mock(
                wraps=defaults.evidence_quality_validator
            ),
            grounding_context_builder=Mock(
                wraps=defaults.grounding_context_builder
            ),
        )

    def _pipeline(self, dependencies, execution, evaluation, recovery):
        return OrchestrationPipeline(
            dependencies=dependencies,
            analyze=Mock(
                return_value={"task_type": "general", "confidence": 0.9}
            ),
            route=Mock(
                return_value={
                    "strategy": "general",
                    "model": "test-model",
                    "candidates": ["test-model"],
                    "optimization": {
                        "status": "not_applied",
                        "exploration": False,
                    },
                }
            ),
            evaluate=Mock(return_value=evaluation),
            recover=Mock(return_value=recovery),
            fallback=Mock(return_value=execution),
        )

    def test_pipeline_runs_through_explicit_stage_boundaries(self):
        dependencies = self._dependencies()
        execution = _execution(2)
        evaluation = _evaluation()
        recovery = _recovery(execution, evaluation)
        memory = Mock(wraps=OutcomeMemory())

        pipeline = self._pipeline(
            dependencies,
            execution,
            evaluation,
            recovery,
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
        dependencies.evidence_normalizer.normalize_result.assert_called_once()
        dependencies.evidence_quality_validator.validate_result.assert_called_once()
        dependencies.grounding_context_builder.build_result.assert_called_once()
        memory.record.assert_called_once()

    def test_execution_and_recovery_receive_same_budget(self):
        dependencies = self._dependencies()
        execution = _execution(3)
        evaluation = _evaluation()
        seen = {}

        def fallback(**kwargs):
            seen["execution_budget"] = kwargs["execution_budget"]
            return execution

        def recover(**kwargs):
            seen["recovery_budget"] = kwargs["execution_budget"]
            return _recovery(execution, evaluation)

        pipeline = OrchestrationPipeline(
            dependencies=dependencies,
            analyze=Mock(
                return_value={"task_type": "general", "confidence": 0.9}
            ),
            route=Mock(
                return_value={
                    "strategy": "general",
                    "model": "test-model",
                    "candidates": ["test-model"],
                    "optimization": {
                        "status": "not_applied",
                        "exploration": False,
                    },
                }
            ),
            evaluate=Mock(return_value=evaluation),
            recover=recover,
            fallback=fallback,
        )
        budget = ExecutionBudget(max_attempts=3)
        memory = Mock(wraps=OutcomeMemory())

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
        pipeline = OrchestrationPipeline(
            dependencies=dependencies,
            analyze=Mock(
                return_value={"task_type": "general", "confidence": 0.9}
            ),
            route=Mock(
                return_value={
                    "strategy": "general",
                    "model": "test-model",
                    "candidates": ["test-model"],
                    "optimization": {
                        "status": "not_applied",
                        "exploration": False,
                    },
                }
            ),
            evaluate=Mock(),
            recover=Mock(),
            fallback=Mock(),
        )
        memory = Mock(wraps=OutcomeMemory())

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


if __name__ == "__main__":
    unittest.main()
