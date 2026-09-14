from dataclasses import dataclass

from backend.app.controls.human_in_the_loop import HumanApprovalPolicy
from backend.app.models.provider_invocation_executor import ProviderInvocationExecutor
from backend.app.reality.context_requirements import RealityContextRequirementDetector
from backend.app.reality.evidence_normalization_consumer import EvidenceNormalizationConsumer
from backend.app.reality.evidence_normalizer import RetrievalEvidenceNormalizer
from backend.app.reality.evidence_quality import EvidenceQualityValidator
from backend.app.reality.evidence_quality_validation_normalizer import EvidenceQualityValidationResultNormalizer
from backend.app.reality.grounded_result import GroundedResultEnvelopeBuilder
from backend.app.reality.grounding_context import EvidenceGroundingContextBuilder
from backend.app.reality.grounding_context_consumer import GroundingContextConsumer
from backend.app.reality.grounding_context_normalizer import GroundingContextNormalizer
from backend.app.reality.grounding_context_consumption_normalizer import GroundingContextConsumptionResultNormalizer
from backend.app.reality.retrieval_contract import RealityRetrievalContract
from backend.app.reality.retrieval_engine import RealityRetrievalEngine, UnconfiguredRetrievalProvider
from backend.app.reality.retrieval_provider_executor import RetrievalProviderExecutor
from backend.app.reality.retrieval_provider_registry import RetrievalProviderRegistry
from backend.app.reality.retrieval_provider_selector import RegistryRetrievalProviderSelector
from backend.app.reality.retrieval_result_consumer import RetrievalResultConsumer
from backend.app.reality.retrieval_result_consumption_normalizer import RetrievalResultConsumptionNormalizer
from backend.app.reality.source_planner import RealitySourcePlanner


@dataclass(frozen=True)
class OrchestrationDependencies:
    """Composition boundary for services used by the orchestration pipeline."""

    context_detector: RealityContextRequirementDetector
    source_planner: RealitySourcePlanner
    retrieval_contract: RealityRetrievalContract
    approval_policy: HumanApprovalPolicy
    retrieval_engine: RealityRetrievalEngine
    retrieval_provider_executor: RetrievalProviderExecutor
    retrieval_provider_registry: RetrievalProviderRegistry
    retrieval_provider_selector: RegistryRetrievalProviderSelector
    retrieval_result_consumer: RetrievalResultConsumer
    retrieval_result_consumption_normalizer: RetrievalResultConsumptionNormalizer
    evidence_normalizer: RetrievalEvidenceNormalizer
    evidence_normalization_consumer: EvidenceNormalizationConsumer
    evidence_quality_validator: EvidenceQualityValidator
    evidence_quality_validation_result_normalizer: EvidenceQualityValidationResultNormalizer
    grounding_context_builder: EvidenceGroundingContextBuilder
    grounding_context_normalizer: GroundingContextNormalizer
    grounding_context_consumer: GroundingContextConsumer
    grounding_context_consumption_normalizer: GroundingContextConsumptionResultNormalizer
    grounded_result_builder: GroundedResultEnvelopeBuilder
    provider_executor: ProviderInvocationExecutor

    @classmethod
    def default(cls) -> "OrchestrationDependencies":
        """Build the production-default dependency graph for the prototype."""
        retrieval_provider_executor = RetrievalProviderExecutor()
        retrieval_provider_registry = RetrievalProviderRegistry(
            providers={},
            default_provider=UnconfiguredRetrievalProvider(),
        )
        retrieval_provider_selector = RegistryRetrievalProviderSelector(
            registry=retrieval_provider_registry,
        )
        return cls(
            context_detector=RealityContextRequirementDetector(),
            source_planner=RealitySourcePlanner(),
            retrieval_contract=RealityRetrievalContract(),
            approval_policy=HumanApprovalPolicy(),
            retrieval_engine=RealityRetrievalEngine(
                provider_executor=retrieval_provider_executor,
                provider_selector=retrieval_provider_selector,
            ),
            retrieval_provider_executor=retrieval_provider_executor,
            retrieval_provider_registry=retrieval_provider_registry,
            retrieval_provider_selector=retrieval_provider_selector,
            retrieval_result_consumer=RetrievalResultConsumer(),
            retrieval_result_consumption_normalizer=RetrievalResultConsumptionNormalizer(),
            evidence_normalizer=RetrievalEvidenceNormalizer(),
            evidence_normalization_consumer=EvidenceNormalizationConsumer(),
            evidence_quality_validator=EvidenceQualityValidator(),
            evidence_quality_validation_result_normalizer=EvidenceQualityValidationResultNormalizer(),
            grounding_context_builder=EvidenceGroundingContextBuilder(),
            grounding_context_normalizer=GroundingContextNormalizer(),
            grounding_context_consumer=GroundingContextConsumer(),
            grounding_context_consumption_normalizer=GroundingContextConsumptionResultNormalizer(),
            grounded_result_builder=GroundedResultEnvelopeBuilder(),
            provider_executor=ProviderInvocationExecutor(),
        )


__all__ = ["OrchestrationDependencies"]
