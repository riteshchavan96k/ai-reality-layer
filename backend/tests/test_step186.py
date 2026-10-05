"""Step 186 — finite freshness windows at every API/domain boundary."""

from dataclasses import replace
from datetime import datetime, timezone

import pytest
from pydantic import ValidationError

from backend.app.api.evidence_reality_state import EvidenceRealityStateRequest
from backend.app.api.reality_state import RealityStateRequest
from backend.app.main import app
from backend.app.orchestrator.dependencies import OrchestrationDependencies
from backend.app.orchestrator.orchestrator import (
    build_reality_state,
    build_reality_state_from_evidence,
)
from backend.app.reality.freshness_policy import (
    is_finite_number,
    is_nonnegative_finite_number,
    is_positive_finite_number,
)
from backend.app.reality.retrieval_contract import (
    RealityRetrievalContract,
    RetrievalRequest,
)
from backend.app.reality.retrieval_provider_request import RetrievalProviderRequest
from backend.app.reality.source_freshness import (
    SourceFreshnessAssessment,
    SourceFreshnessResult,
)
from backend.app.reality.source_freshness_evaluator import SourceFreshnessEvaluator
from backend.app.reality.source_observation import (
    SourceObservation,
    SourceObservationResult,
)
from backend.app.reality.submitted_evidence import SubmittedEvidenceBundle


INVALID_WINDOWS = (
    float("nan"),
    float("inf"),
    float("-inf"),
    10 ** 1000,
    0,
    -1,
    False,
    True,
    "3600",
    None,  # null is tested separately as intentionally allowed.
)
NOW = datetime(2026, 1, 5, tzinfo=timezone.utc)
STALE = "2026-01-01T00:00:00Z"


def documents():
    return [{
        "uri": "https://example.test/original",
        "content": "Company X is operational.",
        "observed_at": STALE,
    }]


def observation():
    return SourceObservationResult.usable_result((
        SourceObservation("id-1", STALE, "submitted_evidence_observation"),
    ))


@pytest.mark.parametrize("value", INVALID_WINDOWS[:-1])
def test_finite_policy_predicate_rejects_invalid_windows(value):
    assert not is_positive_finite_number(value)


@pytest.mark.parametrize("value", (1, 0.25, 3600, 10**9, 1e308))
def test_finite_policy_accepts_positive_finite_window_values(value):
    assert is_finite_number(value)
    assert is_positive_finite_number(value)


@pytest.mark.parametrize(
    "value",
    (float("nan"), float("inf"), float("-inf"), 10**1000, -1, True, "10"),
)
def test_age_measurement_predicate_rejects_nonfinite_or_invalid_values(value):
    assert not is_nonnegative_finite_number(value)


def test_nonnegative_age_accepts_zero():
    assert is_nonnegative_finite_number(0)
    assert is_nonnegative_finite_number(0.5)


@pytest.mark.parametrize("value", INVALID_WINDOWS[:-1])
def test_direct_evidence_api_rejects_invalid_window(value):
    with pytest.raises(ValidationError, match="freshness_max_age_seconds"):
        EvidenceRealityStateRequest(
            task="What is the current status of Company X?",
            documents=documents(),
            freshness_max_age_seconds=value,
        )


@pytest.mark.parametrize("value", INVALID_WINDOWS[:-1])
def test_retrieval_api_rejects_invalid_window(value):
    with pytest.raises(ValidationError, match="freshness_max_age_seconds"):
        RealityStateRequest(
            task="What is the current status of Company X?",
            freshness_max_age_seconds=value,
        )


@pytest.mark.parametrize("value", INVALID_WINDOWS[:-1])
def test_direct_domain_rejects_invalid_window_before_freshness(value):
    with pytest.raises(ValueError, match="freshness_max_age_seconds"):
        SubmittedEvidenceBundle.from_mappings(
            documents()
        ).validate_freshness_policy(value)


@pytest.mark.parametrize("value", INVALID_WINDOWS[:-1])
def test_direct_orchestration_cannot_mark_old_evidence_fresh(value):
    with pytest.raises(ValueError, match="freshness_max_age_seconds"):
        build_reality_state_from_evidence(
            "What is the current status of Company X?",
            documents(),
            freshness_max_age_seconds=value,
        )


@pytest.mark.parametrize("value", INVALID_WINDOWS[:-1])
def test_retrieval_contracts_disallow_nonfinite_or_invalid_window(value):
    with pytest.raises(ValueError, match="positive number"):
        RetrievalRequest(
            query="latest",
            source_type="web",
            freshness_max_age_seconds=value,
        )
    with pytest.raises(ValueError, match="positive number"):
        RetrievalProviderRequest(
            query="latest",
            source_type="web",
            freshness_max_age_seconds=value,
        )
    with pytest.raises(ValueError, match="positive number"):
        RealityRetrievalContract().build(
            "latest",
            {
                "requires_retrieval": True,
                "source_type": "web",
                "freshness_max_age_seconds": value,
            },
        )
    with pytest.raises(ValueError, match="positive number"):
        RetrievalProviderRequest.from_mapping({
            "query": "latest",
            "source_type": "web",
            "freshness_max_age_seconds": value,
        })


@pytest.mark.parametrize("value", INVALID_WINDOWS[:-1])
def test_freshness_evaluator_never_classifies_nonfinite_as_fresh(value):
    evaluator = SourceFreshnessEvaluator(clock=lambda: NOW)
    with pytest.raises(ValueError, match="positive number"):
        evaluator.evaluate_result(observation(), max_age_seconds=value)


@pytest.mark.parametrize(
    "value", (float("nan"), float("inf"), float("-inf"), 10**1000),
)
def test_canonical_freshness_contract_disallows_nonfinite_max_age(value):
    with pytest.raises(ValueError, match="positive number"):
        SourceFreshnessAssessment(
            source_id="id-1",
            observed_at=STALE,
            status="fresh",
            age_seconds=3600,
            max_age_seconds=value,
        )


@pytest.mark.parametrize(
    "value", (float("nan"), float("inf"), float("-inf"), 10**1000),
)
def test_canonical_freshness_contract_disallows_nonfinite_age(value):
    with pytest.raises(ValueError, match="non-negative number"):
        SourceFreshnessAssessment(
            source_id="id-1",
            observed_at=STALE,
            status="unknown",
            reason="no_policy",
            age_seconds=value,
        )


def test_canonical_freshness_mapping_validation_rechecks_nonfinite():
    with pytest.raises(ValueError, match="positive number"):
        SourceFreshnessResult.validate({
            "status": "usable",
            "source_count": 1,
            "assessments": [{
                "source_id": "id-1",
                "status": "fresh",
                "observed_at": STALE,
                "age_seconds": 3600,
                "max_age_seconds": float("inf"),
                "assessment_method": "observation_age",
                "reason": None,
            }],
            "fresh_count": 1,
            "stale_count": 0,
            "unknown_count": 0,
            "freshness_executed": True,
            "reason": None,
        })


def test_direct_evidence_finite_stale_window_is_conservative():
    service = OrchestrationDependencies.default()
    service = replace(
        service,
        source_freshness_evaluator=SourceFreshnessEvaluator(clock=lambda: NOW),
    )
    state = build_reality_state_from_evidence(
        "What is the current status of Company X?",
        documents(),
        freshness_max_age_seconds=3600,
        dependencies=service,
    )
    assert state["freshness"]["stale_count"] == 1
    assert state["freshness"]["fresh_count"] == 0
    assert state["status"] != "supported"


def test_direct_evidence_finite_large_window_is_intentionally_declarative():
    service = replace(
        OrchestrationDependencies.default(),
        source_freshness_evaluator=SourceFreshnessEvaluator(clock=lambda: NOW),
    )
    state = build_reality_state_from_evidence(
        "What is the current status of Company X?",
        documents(),
        freshness_max_age_seconds=3600 * 24 * 5,
        dependencies=service,
    )
    assert state["freshness"]["fresh_count"] == 1
    assert state["status"] == "supported"


def test_null_window_remains_valid_but_does_not_establish_freshness():
    request = EvidenceRealityStateRequest(
        task="What is the current status of Company X?",
        documents=[{
            "uri": "https://example.test/original",
            "content": "Company X is operational.",
        }],
    )
    assert request.freshness_max_age_seconds is None
    assert RealityStateRequest(task="Current status?").freshness_max_age_seconds is None
    assert RetrievalRequest(query="latest", source_type="web").freshness_max_age_seconds is None

    service = replace(
        OrchestrationDependencies.default(),
        source_freshness_evaluator=SourceFreshnessEvaluator(clock=lambda: NOW),
    )
    state = build_reality_state_from_evidence(
        "What is the current status of Company X?",
        documents(),
        dependencies=service,
    )
    assert state["freshness"]["unknown_count"] == 1
    assert state["status"] != "supported"


def test_http_openapi_preserves_separate_optional_fields():
    schemas = app.openapi()["components"]["schemas"]
    for name in ("RealityStateRequest", "EvidenceRealityStateRequest"):
        assert "freshness_max_age_seconds" in schemas[name]["properties"]
        assert "freshness_max_age_seconds" not in schemas[name].get("required", [])
    assert "documents" not in schemas["RealityStateRequest"]["properties"]


@pytest.mark.parametrize("value", (float("nan"), float("inf"), 10**1000))
def test_retrieval_python_entry_stays_rejecting_nonfinite_policy(value):
    with pytest.raises(ValueError, match="positive finite"):
        build_reality_state(
            "What is the current status of Company X?",
            freshness_max_age_seconds=value,
        )
