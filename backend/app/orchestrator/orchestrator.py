import os

from backend.app.analyzer.task_analyzer import analyze_task
from backend.app.router.model_router import route_task
from backend.app.models.registry import get_model_adapter, get_model_provider_name
from backend.app.controls.human_in_the_loop import HumanApprovalPolicy
from backend.app.evaluation.response_evaluator import evaluate_response
from backend.app.evaluation.quality_recovery import recover_with_evaluation
from backend.app.execution.retry_policy import RetryPolicy
from backend.app.execution.fallback_executor import execute_with_fallback
from backend.app.execution.execution_budget import ExecutionBudget
from backend.app.execution.outcome_memory import DEFAULT_OUTCOME_MEMORY, OutcomeMemory
from backend.app.execution.persistent_outcome_memory import PersistentOutcomeMemory
from backend.app.reality.retrieval_engine import RealityRetrievalEngine
from backend.app.reality.submitted_evidence import SubmittedEvidenceBundle
from backend.app.orchestrator.dependencies import OrchestrationDependencies
from backend.app.orchestrator.pipeline import OrchestrationPipeline
from backend.app.orchestrator.result_normalizer import (
    OrchestrationResultNormalizer,
)


DEFAULT_PERSISTENT_MEMORY_PATH = os.getenv(
    "ARL_OUTCOME_MEMORY_PATH",
    "",
)

if DEFAULT_PERSISTENT_MEMORY_PATH:
    DEFAULT_CONFIGURED_MEMORY = PersistentOutcomeMemory(DEFAULT_PERSISTENT_MEMORY_PATH)
else:
    DEFAULT_CONFIGURED_MEMORY = DEFAULT_OUTCOME_MEMORY


def build_reality_state(
    task: str,
    retrieval_engine: RealityRetrievalEngine | None = None,
    dependencies: OrchestrationDependencies | None = None,
    freshness_max_age_seconds: float | int | None = None,
    entity: str | None = None,
) -> dict:
    """Build the canonical Reality State without executing a model."""
    services = dependencies or OrchestrationDependencies.default()
    pipeline = OrchestrationPipeline(
        dependencies=services,
        analyze=analyze_task,
        route=route_task,
        evaluate=evaluate_response,
        recover=recover_with_evaluation,
        fallback=execute_with_fallback,
    )
    return pipeline.build_reality_state(
        task=task,
        retrieval_engine=retrieval_engine,
        freshness_max_age_seconds=freshness_max_age_seconds,
        entity=entity,
    )



def build_reality_state_from_evidence(
    task: str,
    documents: list[dict],
    freshness_max_age_seconds: float | int | None = None,
    dependencies: OrchestrationDependencies | None = None,
    entity: str | None = None,
) -> dict:
    """Build a canonical Reality State from caller-supplied source-scoped evidence."""
    if not isinstance(task, str) or not task.strip():
        raise ValueError("task must be a non-empty string")

    services = dependencies or OrchestrationDependencies.default()
    bundle = SubmittedEvidenceBundle.from_mappings(documents)
    bundle.validate_freshness_policy(freshness_max_age_seconds)
    evidence = bundle.to_evidence()

    raw_quality_result = services.evidence_quality_validator.validate_result(
        evidence
    )
    quality_result = (
        services.evidence_quality_validation_result_normalizer.normalize(
            raw_quality_result
        )
    )

    claim_result = bundle.extract_claims(services.claim_extractor)
    linking = services.claim_evidence_linker.link_result(
        claim_result,
        evidence,
    )
    conflicts = services.claim_conflict_detector.detect_result(claim_result)
    provenance = services.source_provenance_builder.build_result(evidence)
    observation = bundle.build_observations(provenance)
    freshness = services.source_freshness_evaluator.evaluate_result(
        observation,
        max_age_seconds=freshness_max_age_seconds,
    )
    confidence = services.confidence_signal_aggregator.aggregate_result(
        quality_result.to_dict(),
        linking.to_dict(),
        freshness.to_dict(),
        conflicts.to_dict(),
    )
    reality_state = services.reality_state_builder.build_result(
        task,
        evidence,
        claim_result.to_dict(),
        linking.to_dict(),
        provenance.to_dict(),
        observation.to_dict(),
        freshness.to_dict(),
        conflicts.to_dict(),
        confidence.to_dict(),
        entity=entity,
    )
    return reality_state.to_dict()

def orchestrate_task(
    task: str,
    human_approved: bool = False,
    approval_policy: HumanApprovalPolicy | None = None,
    retry_policy: RetryPolicy | None = None,
    execution_budget: ExecutionBudget | None = None,
    outcome_memory: OutcomeMemory | PersistentOutcomeMemory | None = None,
    retrieval_engine: RealityRetrievalEngine | None = None,
    dependencies: OrchestrationDependencies | None = None,
) -> dict:
    """Public orchestration entry point backed by the decomposed pipeline."""
    memory = outcome_memory or DEFAULT_CONFIGURED_MEMORY
    services = dependencies or OrchestrationDependencies.default()
    pipeline = OrchestrationPipeline(
        dependencies=services,
        analyze=analyze_task,
        route=route_task,
        evaluate=evaluate_response,
        recover=recover_with_evaluation,
        fallback=execute_with_fallback,
    )
    result = pipeline.run(
        task=task,
        human_approved=human_approved,
        approval_policy=approval_policy,
        retry_policy=retry_policy or RetryPolicy(),
        execution_budget=execution_budget,
        outcome_memory=memory,
        retrieval_engine=retrieval_engine,
    )
    return OrchestrationResultNormalizer.normalize(result).to_dict()


__all__ = [
    "build_reality_state",
    "build_reality_state_from_evidence",
    "orchestrate_task",
]
