from dataclasses import dataclass

from backend.app.controls.human_in_the_loop import HumanApprovalPolicy
from backend.app.models.provider_invocation_executor import ProviderInvocationExecutor
from backend.app.reality.context_requirements import RealityContextRequirementDetector
from backend.app.reality.evidence_normalizer import RetrievalEvidenceNormalizer
from backend.app.reality.evidence_quality import EvidenceQualityValidator
from backend.app.reality.grounded_result import GroundedResultEnvelopeBuilder
from backend.app.reality.grounding_context import EvidenceGroundingContextBuilder
from backend.app.reality.retrieval_contract import RealityRetrievalContract
from backend.app.reality.retrieval_engine import RealityRetrievalEngine
from backend.app.reality.source_planner import RealitySourcePlanner


@dataclass(frozen=True)
class OrchestrationDependencies:
    """Composition boundary for services used by the orchestration pipeline."""

    context_detector: RealityContextRequirementDetector
    source_planner: RealitySourcePlanner
    retrieval_contract: RealityRetrievalContract
    approval_policy: HumanApprovalPolicy
    retrieval_engine: RealityRetrievalEngine
    evidence_normalizer: RetrievalEvidenceNormalizer
    evidence_quality_validator: EvidenceQualityValidator
    grounding_context_builder: EvidenceGroundingContextBuilder
    grounded_result_builder: GroundedResultEnvelopeBuilder
    provider_executor: ProviderInvocationExecutor

    @classmethod
    def default(cls) -> "OrchestrationDependencies":
        """Build the production-default dependency graph for the prototype."""
        return cls(
            context_detector=RealityContextRequirementDetector(),
            source_planner=RealitySourcePlanner(),
            retrieval_contract=RealityRetrievalContract(),
            approval_policy=HumanApprovalPolicy(),
            retrieval_engine=RealityRetrievalEngine(),
            evidence_normalizer=RetrievalEvidenceNormalizer(),
            evidence_quality_validator=EvidenceQualityValidator(),
            grounding_context_builder=EvidenceGroundingContextBuilder(),
            grounded_result_builder=GroundedResultEnvelopeBuilder(),
            provider_executor=ProviderInvocationExecutor(),
        )


__all__ = ["OrchestrationDependencies"]
