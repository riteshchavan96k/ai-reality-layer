import pytest

from backend.app.api.reality_state import RealityStateRequest, RealityStateResponse
from backend.app.main import app


def test_reality_state_request_does_not_include_solve_only_approval_field():
    assert set(RealityStateRequest.model_fields) == {"task"}


def test_reality_state_response_exposes_canonical_fields():
    assert set(RealityStateResponse.model_fields) == {
        "status",
        "task",
        "evidence",
        "claims",
        "claim_evidence_linking",
        "source_provenance",
        "source_observation",
        "freshness",
        "conflicts",
        "confidence_signals",
        "assembly_method",
        "reason",
    }


def test_reality_state_route_uses_dedicated_http_contracts():
    route = next(route for route in app.routes if route.path == "/api/v1/reality-state")
    assert route.response_model is RealityStateResponse
    assert route.body_field is not None
    assert route.body_field.type_ is RealityStateRequest


def test_reality_state_request_validation_is_bounded():
    with pytest.raises(Exception):
        RealityStateRequest(task="")
    with pytest.raises(Exception):
        RealityStateRequest(task="x" * 10_001)


def test_reality_state_response_rejects_unknown_status():
    with pytest.raises(Exception):
        RealityStateResponse(
            status="unknown_status",
            task="task",
            evidence={},
            claims={},
            claim_evidence_linking={},
            source_provenance={},
            source_observation={},
            freshness={},
            conflicts={},
            confidence_signals={},
            assembly_method="deterministic_signal_snapshot",
        )
