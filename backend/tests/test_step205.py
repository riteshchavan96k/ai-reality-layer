"""Step 205 — canonical Reality State verification metadata foundation."""

from dataclasses import replace
from datetime import datetime, timezone

import pytest

from backend.app.api.reality_state import (
    RealityStateRequest,
    RealityStateResponse,
    RealityVerificationResponse,
)
from backend.app.main import app
from backend.app.orchestrator.dependencies import OrchestrationDependencies
from backend.app.orchestrator.orchestrator import (
    build_reality_state,
    build_reality_state_from_evidence,
)
from backend.app.reality.reality_state import RealityState
from backend.app.reality.reality_state_builder import RealityStateBuilder
from backend.app.reality.reality_verification import (
    MAX_REALITY_VERIFIED_AT_CHARS,
    RealityVerification,
    normalize_reality_verification_time,
)
from backend.app.reality.retrieval_result import RetrievalResultContract


NOW = datetime(2026, 1, 2, 3, 4, 5, tzinfo=timezone.utc)
VERIFIED_AT = "2026-01-02T03:04:05Z"
SOURCE = "https://example.test/company-x"
CONTENT = "Company X launched Feature A."


class _CompletedRetrievalEngine:
    def retrieve(self, contract):
        return RetrievalResultContract.completed(
            contract["request"],
            provider="test-provider",
            sources=[{"uri": SOURCE, "title": "Company X update"}],
            content=CONTENT,
        )


def _dependencies():
    return replace(
        OrchestrationDependencies.default(),
        reality_state_builder=RealityStateBuilder(clock=lambda: NOW),
    )


def _parts():
    return (
        {"status": "usable"},
        {"status": "usable", "claim_count": 1},
        {
            "status": "usable",
            "claim_count": 1,
            "linked_claim_count": 1,
        },
        {"status": "usable", "source_count": 1},
        {"status": "usable", "source_count": 1},
        {
            "status": "usable",
            "source_count": 1,
            "fresh_count": 1,
            "stale_count": 0,
            "unknown_count": 0,
        },
        {"status": "empty", "conflict_count": 0},
    )


def _legacy_state_mapping():
    return {
        "status": "uncertain",
        "task": "What is the current status of Company X?",
        "entity": {
            "status": "specified",
            "name": "Company X",
            "identification_method": "explicit_input",
        },
        "evidence": {},
        "claims": {},
        "claim_evidence_linking": {},
        "source_provenance": {},
        "source_observation": {},
        "freshness": {},
        "conflicts": {},
        "confidence_signals": {},
        "assembly_method": "deterministic_signal_snapshot",
        "reason": None,
    }


def test_completed_verification_is_canonical():
    verification = RealityVerification.completed(VERIFIED_AT)

    assert verification.to_dict() == {
        "status": "completed",
        "verified_at": VERIFIED_AT,
        "verification_method": "deterministic_pipeline_snapshot",
        "reason": None,
    }


def test_verification_timestamp_normalizes_offset_to_utc():
    assert normalize_reality_verification_time(
        "2026-01-02T08:34:05+05:30"
    ) == VERIFIED_AT


@pytest.mark.parametrize(
    ("value", "match"),
    [
        ("", "non-empty ISO-8601"),
        ("   ", "non-empty ISO-8601"),
        ("not-a-time", "valid ISO-8601"),
        ("2026-01-02T03:04:05", "include a timezone"),
        ("2999-01-01T00:00:00Z", "cannot be in the future"),
        (
            "x" * (MAX_REALITY_VERIFIED_AT_CHARS + 1),
            "must not exceed",
        ),
    ],
)
def test_verification_timestamp_rejects_invalid_values(value, match):
    with pytest.raises(ValueError, match=match):
        RealityVerification.completed(value)


def test_not_completed_verification_requires_reason_and_has_no_timestamp():
    verification = RealityVerification.not_completed(
        "reality_state_not_assembled"
    )

    assert verification.to_dict() == {
        "status": "not_completed",
        "verified_at": None,
        "verification_method": "not_completed",
        "reason": "reality_state_not_assembled",
    }


def test_completed_verification_rejects_reason():
    with pytest.raises(
        ValueError,
        match="completed verification cannot contain a reason",
    ):
        RealityVerification(
            status="completed",
            verified_at=VERIFIED_AT,
            verification_method="deterministic_pipeline_snapshot",
            reason="unexpected",
        )


def test_not_completed_verification_rejects_timestamp():
    with pytest.raises(
        ValueError,
        match="not_completed verification cannot contain verified_at",
    ):
        RealityVerification(
            status="not_completed",
            verified_at=VERIFIED_AT,
            verification_method="not_completed",
            reason="not assembled",
        )


def test_not_completed_verification_rejects_missing_reason():
    with pytest.raises(
        ValueError,
        match="not_completed verification requires a non-empty reason",
    ):
        RealityVerification(
            status="not_completed",
            verified_at=None,
            verification_method="not_completed",
            reason=None,
        )


def test_verification_mapping_validation_preserves_canonical_state():
    raw = RealityVerification.completed(VERIFIED_AT).to_dict()

    result = RealityVerification.validate(raw)

    assert result == RealityVerification.completed(VERIFIED_AT)


def test_verification_mapping_requires_complete_shape():
    with pytest.raises(
        ValueError,
        match="verification is missing required fields",
    ):
        RealityVerification.validate(
            {
                "status": "completed",
                "verified_at": VERIFIED_AT,
            }
        )


def test_legacy_reality_state_mapping_does_not_invent_verification_time():
    state = RealityState.validate(_legacy_state_mapping())

    assert state.verification.status == "not_completed"
    assert state.verification.verified_at is None
    assert state.verification.reason == "verification_metadata_unavailable"


def test_direct_reality_state_constructor_preserves_legacy_default_safely():
    state = RealityState(
        "uncertain",
        "task",
        {},
        {},
        {},
        {},
        {},
        {},
        {},
        {},
    )

    assert state.verification.status == "not_completed"
    assert state.verification.verified_at is None


def test_builder_stamps_completed_verification_from_injected_clock():
    builder = RealityStateBuilder(clock=lambda: NOW)
    confidence = {
        "status": "supported",
        "evidence_usable": True,
        "claim_coverage": 1.0,
    }

    state = builder.build_result(
        "task",
        *_parts(),
        confidence,
    )

    assert state.verification.status == "completed"
    assert state.verification.verified_at == VERIFIED_AT
    assert state.verification.verification_method == (
        "deterministic_pipeline_snapshot"
    )


def test_builder_rejects_naive_verification_clock():
    builder = RealityStateBuilder(
        clock=lambda: datetime(2026, 1, 2, 3, 4, 5)
    )
    confidence = {"status": "uncertain"}

    with pytest.raises(
        ValueError,
        match="clock must return a timezone-aware datetime",
    ):
        builder.build_result(
            "task",
            *_parts(),
            confidence,
        )


def test_builder_rejects_non_datetime_verification_clock():
    builder = RealityStateBuilder(clock=lambda: "2026-01-02T03:04:05Z")
    confidence = {"status": "uncertain"}

    with pytest.raises(
        ValueError,
        match="clock must return a timezone-aware datetime",
    ):
        builder.build_result(
            "task",
            *_parts(),
            confidence,
        )


def test_unavailable_reality_can_still_have_completed_verification():
    builder = RealityStateBuilder(clock=lambda: NOW)
    confidence = {
        "status": "unavailable",
        "reason": "confidence_signals_unavailable",
    }

    state = builder.build_result(
        "task",
        *_parts(),
        confidence,
    )

    assert state.status == "unavailable"
    assert state.reason == "confidence_signals_unavailable"
    assert state.verification.status == "completed"
    assert state.verification.verified_at == VERIFIED_AT


def test_retrieval_backed_snapshot_has_completed_verification_metadata():
    state = build_reality_state(
        "What is the current status of Company X?",
        retrieval_engine=_CompletedRetrievalEngine(),
        dependencies=_dependencies(),
        entity="Company X",
    )

    assert state["verification"] == {
        "status": "completed",
        "verified_at": VERIFIED_AT,
        "verification_method": "deterministic_pipeline_snapshot",
        "reason": None,
    }


def test_submitted_evidence_snapshot_has_completed_verification_metadata():
    state = build_reality_state_from_evidence(
        "What is the current status of Company X?",
        [
            {
                "uri": SOURCE,
                "content": CONTENT,
                "observed_at": "2026-01-01T00:00:00Z",
            }
        ],
        dependencies=_dependencies(),
        entity="Company X",
    )

    assert state["verification"]["status"] == "completed"
    assert state["verification"]["verified_at"] == VERIFIED_AT
    assert state["source_observation"]["observations"][0]["observed_at"] == (
        "2026-01-01T00:00:00Z"
    )


def test_verification_time_is_distinct_from_source_observation_time():
    state = build_reality_state_from_evidence(
        "What is the current status of Company X?",
        [
            {
                "uri": SOURCE,
                "content": CONTENT,
                "observed_at": "2026-01-01T00:00:00Z",
            }
        ],
        dependencies=_dependencies(),
    )

    assert state["verification"]["verified_at"] == VERIFIED_AT
    assert state["verification"]["verified_at"] != (
        state["source_observation"]["observations"][0]["observed_at"]
    )


def test_verification_is_output_metadata_not_caller_controlled_input():
    assert "verification" not in RealityStateRequest.model_fields
    assert "verified_at" not in RealityStateRequest.model_fields

    with pytest.raises(Exception):
        RealityStateRequest(
            task="Current status?",
            verification={
                "status": "completed",
                "verified_at": VERIFIED_AT,
            },
        )


def test_reality_state_response_exposes_typed_verification_contract():
    field = RealityStateResponse.model_fields["verification"]

    assert field.annotation is RealityVerificationResponse


def test_openapi_documents_verification_as_output_only():
    schema = app.openapi()
    request = schema["components"]["schemas"]["RealityStateRequest"]
    response = schema["components"]["schemas"]["RealityStateResponse"]

    assert "verification" not in request["properties"]
    assert response["properties"]["verification"]["$ref"].endswith(
        "/RealityVerificationResponse"
    )


def test_reality_state_serialization_places_verification_near_identity_metadata():
    builder = RealityStateBuilder(clock=lambda: NOW)
    confidence = {"status": "uncertain"}
    state = builder.build(
        "task",
        *_parts(),
        confidence,
        entity="Company X",
    )

    keys = list(state)
    assert keys[:4] == [
        "status",
        "task",
        "entity",
        "verification",
    ]
