from dataclasses import dataclass
import os

from backend.app.controls.human_in_the_loop import HumanApprovalPolicy
from backend.app.models.provider_invocation_executor import ProviderInvocationExecutor
from backend.app.reality.context_requirements import RealityContextRequirementDetector
from backend.app.reality.claim_evidence_linker import ClaimEvidenceLinker
from backend.app.reality.claim_extractor import EvidenceClaimExtractor
from backend.app.reality.claim_extraction_normalizer import ClaimExtractionResultNormalizer
from backend.app.reality.claim_conflict_detector import ClaimConflictDetector
from backend.app.reality.confidence_signal_aggregator import RealityConfidenceSignalAggregator
from backend.app.reality.reality_state_builder import RealityStateBuilder
from backend.app.reality.evidence_normalization_consumer import EvidenceNormalizationConsumer
from backend.app.reality.evidence_normalization_consumption_normalizer import (
    EvidenceNormalizationConsumptionNormalizer,
)
from backend.app.reality.evidence_normalizer import RetrievalEvidenceNormalizer
from backend.app.reality.evidence_quality import EvidenceQualityValidator
from backend.app.reality.evidence_quality_validation_normalizer import EvidenceQualityValidationResultNormalizer
from backend.app.reality.grounded_result import GroundedResultEnvelopeBuilder
from backend.app.reality.grounding_context import EvidenceGroundingContextBuilder
from backend.app.reality.grounding_context_consumer import GroundingContextConsumer
from backend.app.reality.grounding_context_normalizer import GroundingContextNormalizer
from backend.app.reality.grounding_context_consumption_normalizer import GroundingContextConsumptionResultNormalizer
from backend.app.reality.grounding_execution_authorization_consumer import GroundingExecutionAuthorizationConsumer
from backend.app.reality.grounding_execution_authorization_consumption_decision_evaluator import GroundingExecutionAuthorizationConsumptionDecisionEvaluator
from backend.app.reality.grounding_execution_authorization_consumption_decision_result_consumption import GroundingExecutionAuthorizationConsumptionDecisionResultConsumer
from backend.app.reality.grounding_execution_authorization_consumption_decision_result_normalizer import GroundingExecutionAuthorizationConsumptionDecisionResultNormalizer
from backend.app.reality.grounding_execution_authorization_consumption_decision_result_consumption_result_normalizer import GroundingExecutionAuthorizationConsumptionDecisionResultConsumptionResultNormalizer
from backend.app.reality.grounding_execution_authorization_consumption_decision_result_consumption_result_decision_evaluator import GroundingExecutionAuthorizationConsumptionDecisionResultConsumptionResultDecisionEvaluator
from backend.app.reality.grounding_execution_authorization_consumption_decision_result_consumption_result_decision_result_normalizer import GroundingExecutionAuthorizationConsumptionDecisionResultConsumptionResultDecisionResultNormalizer
from backend.app.reality.grounding_execution_authorization_consumption_decision_result_consumption_result_decision_result_consumption import GroundingExecutionAuthorizationConsumptionDecisionResultConsumptionResultDecisionResultConsumer
from backend.app.reality.grounding_execution_authorization_consumption_decision_result_consumption_result_decision_result_consumption_result_normalizer import GroundingExecutionAuthorizationConsumptionDecisionResultConsumptionResultDecisionResultConsumptionResultNormalizer
from backend.app.reality.grounding_execution_authorization_consumption_result_normalizer import GroundingExecutionAuthorizationConsumptionResultNormalizer
from backend.app.reality.grounding_execution_authorization_evaluator import GroundingExecutionAuthorizationEvaluator
from backend.app.reality.grounding_execution_context_normalizer import GroundingExecutionContextNormalizer
from backend.app.reality.grounding_execution_context_consumption import GroundingExecutionContextConsumer
from backend.app.reality.grounding_execution_context_consumption_decision_evaluator import GroundingExecutionContextConsumptionDecisionEvaluator
from backend.app.reality.grounding_execution_context_consumption_normalizer import GroundingExecutionContextConsumptionResultNormalizer
from backend.app.reality.grounding_execution_gate import GroundingExecutionGate
from backend.app.reality.grounding_execution_gate_normalizer import GroundingExecutionGateResultNormalizer
from backend.app.reality.retrieval_contract import RealityRetrievalContract
from backend.app.reality.retrieval_engine import RealityRetrievalEngine, UnconfiguredRetrievalProvider
from backend.app.reality.http_retrieval_provider import HttpRetrievalProvider
from backend.app.reality.retrieval_provider_executor import RetrievalProviderExecutor
from backend.app.reality.retrieval_provider_registry import RetrievalProviderRegistry
from backend.app.reality.retrieval_provider_capabilities import RetrievalProviderCapabilities
from backend.app.reality.retrieval_provider_descriptor import RetrievalProviderDescriptor
from backend.app.reality.retrieval_provider_selector import RegistryRetrievalProviderSelector
from backend.app.reality.retrieval_result_consumer import RetrievalResultConsumer
from backend.app.reality.retrieval_result_consumption_normalizer import RetrievalResultConsumptionNormalizer
from backend.app.reality.source_planner import RealitySourcePlanner
from backend.app.reality.source_observation_builder import SourceObservationBuilder
from backend.app.reality.source_freshness_evaluator import SourceFreshnessEvaluator
from backend.app.reality.source_provenance_builder import SourceProvenanceBuilder


@dataclass(frozen=True)
class OrchestrationDependencies:
    """Composition boundary for services used by the orchestration pipeline."""

    context_detector: RealityContextRequirementDetector
    claim_extractor: EvidenceClaimExtractor
    claim_extraction_result_normalizer: ClaimExtractionResultNormalizer
    claim_conflict_detector: ClaimConflictDetector
    confidence_signal_aggregator: RealityConfidenceSignalAggregator
    reality_state_builder: RealityStateBuilder
    claim_evidence_linker: ClaimEvidenceLinker
    source_provenance_builder: SourceProvenanceBuilder
    source_observation_builder: SourceObservationBuilder
    source_freshness_evaluator: SourceFreshnessEvaluator
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
    evidence_normalization_consumption_normalizer: EvidenceNormalizationConsumptionNormalizer
    evidence_quality_validator: EvidenceQualityValidator
    evidence_quality_validation_result_normalizer: EvidenceQualityValidationResultNormalizer
    grounding_context_builder: EvidenceGroundingContextBuilder
    grounding_context_normalizer: GroundingContextNormalizer
    grounding_context_consumer: GroundingContextConsumer
    grounding_context_consumption_normalizer: GroundingContextConsumptionResultNormalizer
    grounding_execution_gate: GroundingExecutionGate
    grounding_execution_gate_normalizer: GroundingExecutionGateResultNormalizer
    grounding_execution_context_normalizer: GroundingExecutionContextNormalizer
    grounding_execution_context_consumer: GroundingExecutionContextConsumer
    grounding_execution_context_consumption_normalizer: GroundingExecutionContextConsumptionResultNormalizer
    grounding_execution_context_consumption_decision_evaluator: GroundingExecutionContextConsumptionDecisionEvaluator
    grounding_execution_authorization_evaluator: GroundingExecutionAuthorizationEvaluator
    grounding_execution_authorization_consumer: GroundingExecutionAuthorizationConsumer
    grounding_execution_authorization_consumption_result_normalizer: GroundingExecutionAuthorizationConsumptionResultNormalizer
    grounding_execution_authorization_consumption_decision_evaluator: GroundingExecutionAuthorizationConsumptionDecisionEvaluator
    grounding_execution_authorization_consumption_decision_result_normalizer: GroundingExecutionAuthorizationConsumptionDecisionResultNormalizer
    grounding_execution_authorization_consumption_decision_result_consumer: GroundingExecutionAuthorizationConsumptionDecisionResultConsumer
    grounding_execution_authorization_consumption_decision_result_consumption_result_normalizer: GroundingExecutionAuthorizationConsumptionDecisionResultConsumptionResultNormalizer
    grounding_execution_authorization_consumption_decision_result_consumption_result_decision_evaluator: GroundingExecutionAuthorizationConsumptionDecisionResultConsumptionResultDecisionEvaluator
    grounding_execution_authorization_consumption_decision_result_consumption_result_decision_result_normalizer: GroundingExecutionAuthorizationConsumptionDecisionResultConsumptionResultDecisionResultNormalizer
    grounding_execution_authorization_consumption_decision_result_consumption_result_decision_result_consumer: GroundingExecutionAuthorizationConsumptionDecisionResultConsumptionResultDecisionResultConsumer
    grounding_execution_authorization_consumption_decision_result_consumption_result_decision_result_consumption_result_normalizer: GroundingExecutionAuthorizationConsumptionDecisionResultConsumptionResultDecisionResultConsumptionResultNormalizer
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
        configured_endpoint = os.getenv("ARL_HTTP_RETRIEVAL_ENDPOINT_TEMPLATE", "").strip()
        if configured_endpoint:
            configured_provider = HttpRetrievalProvider(configured_endpoint)
            capabilities = RetrievalProviderCapabilities(
                source_types=("live_web", "web_or_official_source"),
                temporal_scopes=("current", "unspecified"),
            )
            retrieval_provider_registry.register_descriptor(
                "live_web",
                RetrievalProviderDescriptor(
                    name=configured_provider.provider_name,
                    capabilities=capabilities,
                    provider=configured_provider,
                ),
            )
            retrieval_provider_registry.register_descriptor(
                "web_or_official_source",
                RetrievalProviderDescriptor(
                    name=configured_provider.provider_name,
                    capabilities=capabilities,
                    provider=configured_provider,
                ),
            )
        retrieval_provider_selector = RegistryRetrievalProviderSelector(
            registry=retrieval_provider_registry,
        )
        return cls(
            context_detector=RealityContextRequirementDetector(),
            claim_extractor=EvidenceClaimExtractor(),
            claim_extraction_result_normalizer=ClaimExtractionResultNormalizer(),
            claim_conflict_detector=ClaimConflictDetector(),
            confidence_signal_aggregator=RealityConfidenceSignalAggregator(),
            reality_state_builder=RealityStateBuilder(),
            claim_evidence_linker=ClaimEvidenceLinker(),
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
            evidence_normalization_consumption_normalizer=EvidenceNormalizationConsumptionNormalizer(),
            evidence_quality_validator=EvidenceQualityValidator(),
            evidence_quality_validation_result_normalizer=EvidenceQualityValidationResultNormalizer(),
            grounding_context_builder=EvidenceGroundingContextBuilder(),
            grounding_context_normalizer=GroundingContextNormalizer(),
            grounding_context_consumer=GroundingContextConsumer(),
            grounding_context_consumption_normalizer=GroundingContextConsumptionResultNormalizer(),
            grounding_execution_gate=GroundingExecutionGate(),
            grounding_execution_gate_normalizer=GroundingExecutionGateResultNormalizer(),
            grounding_execution_context_normalizer=GroundingExecutionContextNormalizer(),
            grounding_execution_context_consumer=GroundingExecutionContextConsumer(),
            grounding_execution_context_consumption_normalizer=GroundingExecutionContextConsumptionResultNormalizer(),
            grounding_execution_context_consumption_decision_evaluator=GroundingExecutionContextConsumptionDecisionEvaluator(),
            grounding_execution_authorization_evaluator=GroundingExecutionAuthorizationEvaluator(),
            grounding_execution_authorization_consumer=GroundingExecutionAuthorizationConsumer(),
            grounding_execution_authorization_consumption_result_normalizer=GroundingExecutionAuthorizationConsumptionResultNormalizer(),
            grounding_execution_authorization_consumption_decision_evaluator=GroundingExecutionAuthorizationConsumptionDecisionEvaluator(),
            grounding_execution_authorization_consumption_decision_result_normalizer=GroundingExecutionAuthorizationConsumptionDecisionResultNormalizer(),
            grounding_execution_authorization_consumption_decision_result_consumer=GroundingExecutionAuthorizationConsumptionDecisionResultConsumer(),
            grounding_execution_authorization_consumption_decision_result_consumption_result_normalizer=GroundingExecutionAuthorizationConsumptionDecisionResultConsumptionResultNormalizer(),
            grounding_execution_authorization_consumption_decision_result_consumption_result_decision_evaluator=GroundingExecutionAuthorizationConsumptionDecisionResultConsumptionResultDecisionEvaluator(),
            grounding_execution_authorization_consumption_decision_result_consumption_result_decision_result_normalizer=GroundingExecutionAuthorizationConsumptionDecisionResultConsumptionResultDecisionResultNormalizer(),
            grounding_execution_authorization_consumption_decision_result_consumption_result_decision_result_consumer=GroundingExecutionAuthorizationConsumptionDecisionResultConsumptionResultDecisionResultConsumer(),
            grounding_execution_authorization_consumption_decision_result_consumption_result_decision_result_consumption_result_normalizer=GroundingExecutionAuthorizationConsumptionDecisionResultConsumptionResultDecisionResultConsumptionResultNormalizer(),
            grounded_result_builder=GroundedResultEnvelopeBuilder(),
            provider_executor=ProviderInvocationExecutor(),
        )
