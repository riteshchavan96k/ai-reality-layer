import unittest
from unittest.mock import Mock, patch

from backend.app.controls.human_in_the_loop import HumanApprovalPolicy
from backend.app.models.provider_invocation_executor import ProviderInvocationExecutor
from backend.app.orchestrator.dependencies import OrchestrationDependencies
from backend.app.orchestrator.orchestrator import orchestrate_task
from backend.app.reality.context_requirements import RealityContextRequirementDetector
from backend.app.reality.evidence_normalizer import RetrievalEvidenceNormalizer
from backend.app.reality.evidence_quality import EvidenceQualityValidator
from backend.app.reality.grounded_result import GroundedResultEnvelopeBuilder
from backend.app.reality.grounding_context import EvidenceGroundingContextBuilder
from backend.app.reality.retrieval_contract import RealityRetrievalContract
from backend.app.reality.retrieval_engine import RealityRetrievalEngine
from backend.app.reality.source_planner import RealitySourcePlanner


class Step56Tests(unittest.TestCase):
    def test_default_dependency_graph_contains_expected_services(self):
        dependencies = OrchestrationDependencies.default()

        self.assertIsInstance(dependencies.context_detector, RealityContextRequirementDetector)
        self.assertIsInstance(dependencies.source_planner, RealitySourcePlanner)
        self.assertIsInstance(dependencies.retrieval_contract, RealityRetrievalContract)
        self.assertIsInstance(dependencies.approval_policy, HumanApprovalPolicy)
        self.assertIsInstance(dependencies.retrieval_engine, RealityRetrievalEngine)
        self.assertIsInstance(dependencies.evidence_normalizer, RetrievalEvidenceNormalizer)
        self.assertIsInstance(
            dependencies.evidence_quality_validator,
            EvidenceQualityValidator,
        )
        self.assertIsInstance(
            dependencies.grounding_context_builder,
            EvidenceGroundingContextBuilder,
        )
        self.assertIsInstance(
            dependencies.grounded_result_builder,
            GroundedResultEnvelopeBuilder,
        )
        self.assertIsInstance(
            dependencies.provider_executor,
            ProviderInvocationExecutor,
        )

    def test_orchestrator_uses_injected_services_without_constructing_defaults(self):
        context_detector = Mock()
        context_detector.detect.return_value = {
            "needs_current_info": False,
            "needs_external_evidence": False,
            "temporal_scope": "unspecified",
        }
        source_planner = Mock()
        source_planner.plan.return_value = {
            "source_type": "model_knowledge",
            "priority": "optional",
            "temporal_scope": "unspecified",
            "requires_retrieval": False,
            "status": "planned",
        }
        retrieval_contract = Mock()
        retrieval_contract.build.return_value = {
            "status": "not_required",
            "request": {"required": False},
        }
        approval_policy = Mock()
        approval_policy.evaluate.return_value = {
            "required": False,
            "risk_level": "normal",
            "mode": "test",
        }
        retrieval_engine = Mock()
        retrieval_engine.retrieve.return_value = {
            "status": "not_required",
            "sources": [],
            "content": "",
        }
        evidence_normalizer = Mock()
        evidence_normalizer.normalize.return_value = {
            "status": "usable",
            "sources": [],
            "content": "",
        }
        evidence_quality_validator = Mock()
        evidence_quality_validator.validate.return_value = {
            "status": "usable",
            "issues": [],
        }
        grounding_context_builder = Mock()
        grounding_context_builder.build.return_value = {
            "status": "not_required",
            "source_count": 0,
            "sources": [],
            "content": "",
        }
        grounded_result_builder = Mock()
        grounded_result_builder.build.return_value = {
            "status": "ungrounded",
            "result": {"text": "ok"},
        }
        provider_executor = Mock()

        dependencies = OrchestrationDependencies(
            context_detector=context_detector,
            source_planner=source_planner,
            retrieval_contract=retrieval_contract,
            approval_policy=approval_policy,
            retrieval_engine=retrieval_engine,
            evidence_normalizer=evidence_normalizer,
            evidence_quality_validator=evidence_quality_validator,
            grounding_context_builder=grounding_context_builder,
            grounded_result_builder=grounded_result_builder,
            provider_executor=provider_executor,
        )

        execution = {
            "status": "success",
            "model": "test-model",
            "attempts": 1,
            "total_attempts": 1,
            "budget_limit": 1,
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
        outcome_memory = Mock()
        outcome_memory.record.return_value = {"status": "recorded"}

        with patch(
            "backend.app.orchestrator.orchestrator.analyze_task",
            return_value={"task_type": "general", "confidence": 0.9},
        ), patch(
            "backend.app.orchestrator.orchestrator.route_task",
            return_value={
                "strategy": "general",
                "model": "test-model",
                "candidates": ["test-model"],
                "optimization": {"status": "not_applied", "exploration": False},
            },
        ), patch(
            "backend.app.orchestrator.orchestrator.execute_with_fallback",
            return_value=execution,
        ) as fallback, patch(
            "backend.app.orchestrator.orchestrator.evaluate_response",
            return_value=evaluation,
        ), patch(
            "backend.app.orchestrator.orchestrator.recover_with_evaluation",
            return_value=recovery,
        ):
            result = orchestrate_task(
                "test task",
                human_approved=True,
                outcome_memory=outcome_memory,
                dependencies=dependencies,
            )

        self.assertEqual(result["status"], "orchestrated")
        context_detector.detect.assert_called_once_with("test task")
        source_planner.plan.assert_called_once()
        retrieval_contract.build.assert_called_once()
        approval_policy.evaluate.assert_called_once()
        retrieval_engine.retrieve.assert_called_once()
        evidence_normalizer.normalize.assert_called_once()
        evidence_quality_validator.validate.assert_called_once()
        grounding_context_builder.build.assert_called_once()
        grounded_result_builder.build.assert_called_once()
        fallback.assert_called_once()
        self.assertIs(dependencies.provider_executor, provider_executor)


if __name__ == "__main__":
    unittest.main()
