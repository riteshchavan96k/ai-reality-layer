from backend.app.evaluation.quality_recovery import recover_with_evaluation
from backend.app.execution.execution_budget import ExecutionBudget
from backend.app.execution.fallback_executor import execute_with_fallback
from backend.app.execution.retry_policy import RetryPolicy
from backend.app.models.mock_model import MockModelAdapter
from backend.app.reality.claim_evidence_linking import (
    ClaimEvidenceLink,
    ClaimEvidenceLinkingResult,
)
from backend.app.reality.claim_extractor import EvidenceClaimExtractor
from backend.app.reality.evidence_normalization_consumer import (
    EvidenceNormalizationConsumer,
)
from backend.app.reality.evidence_normalization_consumption import (
    EvidenceNormalizationConsumption,
)
from backend.app.reality.evidence_normalization_consumption_normalizer import (
    EvidenceNormalizationConsumptionNormalizer,
)
from backend.app.reality.evidence_normalization_consumption_result import (
    EvidenceNormalizationConsumptionResult,
)
from backend.app.reality.grounding_context import EvidenceGroundingContextBuilder
from backend.app.reality.grounding_context_normalizer import GroundingContextNormalizer


class _LegacyAdapter:
    def __init__(self, text="Python recursion explained"):
        self.text = text

    def generate(self, task):
        return {
            "text": self.text,
            "model": "legacy-model",
            "provider": "legacy-provider",
        }


def test_typed_evidence_consumption_result_crosses_step153_boundary():
    raw = EvidenceNormalizationConsumptionResult.usable_result("completed")

    normalized = EvidenceNormalizationConsumptionNormalizer.normalize(raw)

    assert isinstance(normalized, EvidenceNormalizationConsumption)
    assert normalized.status == "usable"
    assert normalized.evidence_status == "completed"
    assert normalized.usable is True
    assert normalized.consumption_executed is True


def test_claim_linking_factories_and_derived_unlinked_count_are_available():
    link = ClaimEvidenceLink(
        claim_text="Claim A",
        source_ref="https://example.test/a",
    )

    result = ClaimEvidenceLinkingResult.usable_result(
        (link,),
        claim_count=2,
        source_count=1,
    )

    assert result.linked_claim_count == 1
    assert result.unlinked_claim_count == 1
    assert result.to_dict()["unlinked_claim_count"] == 1
    assert ClaimEvidenceLinkingResult.empty_result().status == "empty"
    assert (
        ClaimEvidenceLinkingResult.unavailable_result("no_evidence").status
        == "unavailable"
    )


def test_claim_extractor_splits_sentences_and_deduplicates():
    result = EvidenceClaimExtractor().extract_result(
        {
            "status": "completed",
            "content": "Alpha is true. Beta is current! Alpha is true.",
            "sources": [{"uri": "https://example.test/source"}],
        }
    )

    assert [claim.text for claim in result.claims] == [
        "Alpha is true.",
        "Beta is current!",
    ]


def test_grounding_normalizer_preserves_legacy_execution_default():
    result = GroundingContextNormalizer.normalize(
        {
            "status": "not_available",
            "task": "stable task",
            "content": None,
            "sources": [],
            "source_count": 0,
        }
    )

    assert result.grounding_executed is True


def test_completed_normalized_evidence_can_become_ready_grounding():
    result = EvidenceGroundingContextBuilder().build_result(
        "current task",
        {
            "status": "completed",
            "content": "Fresh evidence",
            "sources": [
                {
                    "title": "Source",
                    "uri": "https://example.test/source",
                }
            ],
        },
    )

    assert result.status == "ready"
    assert result.source_count == 1


def test_unsupported_evidence_status_fails_closed_as_canonical_unknown():
    result = EvidenceNormalizationConsumer().consume(
        {
            "status": "future_state",
            "sources": [],
            "content": None,
        }
    )

    assert result.status == "rejected"
    assert result.evidence_status == "unknown"
    assert result.reason == "unsupported_evidence_status"


def test_mock_model_reads_canonical_grounding_status_key():
    response = MockModelAdapter().generate(
        "task",
        context={
            "grounding_status": "ready",
            "source_count": 2,
        },
    )

    assert response["grounding"] == {
        "status": "ready",
        "source_count": 2,
        "grounded": True,
    }


def test_fallback_keeps_legacy_generate_task_signature_supported():
    result = execute_with_fallback(
        task="Explain recursion",
        model_names=["legacy-model"],
        adapter_resolver=lambda _: _LegacyAdapter(),
        retry_policy=RetryPolicy(max_attempts=1),
    )

    assert result["status"] == "success"
    assert result["model"] == "legacy-model"


def test_quality_recovery_keeps_legacy_generate_task_signature_supported():
    initial_execution = {
        "status": "success",
        "model": "initial-model",
        "attempts": 1,
        "total_attempts": 1,
        "budget_limit": 2,
        "attempts_by_model": {"initial-model": 1},
        "fallback_used": False,
        "result": {
            "text": "unrelated response",
            "model": "initial-model",
            "provider": "legacy-provider",
        },
        "errors": None,
    }
    budget = ExecutionBudget(max_attempts=2, used_attempts=1)

    result = recover_with_evaluation(
        task="Explain Python recursion",
        candidates=["initial-model", "legacy-model"],
        adapter_resolver=lambda name: (
            _LegacyAdapter() if name == "legacy-model" else None
        ),
        analysis={"task_type": "programming"},
        routing={"model": "initial-model"},
        initial_execution=initial_execution,
        initial_evaluation={"score": 0.2, "status": "review"},
        retry_policy=RetryPolicy(max_attempts=1),
        execution_budget=budget,
    )

    assert result["used"] is True
    assert result["best"]["model"] == "legacy-model"
    assert result["best"]["execution"]["status"] == "success"
