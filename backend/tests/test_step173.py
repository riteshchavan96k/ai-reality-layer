import pytest

from backend.app.api.solve import SolveRequest, SolveResponse
from backend.app.main import SolveRequest as MainSolveRequest
from backend.app.main import app


def _approval_response(**extra):
    value = {
        "status": "awaiting_human_approval",
        "analysis": {},
        "routing": {},
        "approval": {
            "required": True,
            "risk_level": "high",
        },
        "trace": [],
    }
    value.update(extra)
    return value


def test_solve_request_contract_is_dedicated_and_backward_compatible():
    assert MainSolveRequest is SolveRequest
    assert set(SolveRequest.model_fields) == {
        "task",
        "human_approved",
    }


def test_solve_request_rejects_unknown_fields():
    with pytest.raises(Exception):
        SolveRequest(
            task="Tell me about AI",
            human_approved=False,
            unsupported=True,
        )


def test_solve_request_validation_remains_bounded():
    with pytest.raises(Exception):
        SolveRequest(task="")
    with pytest.raises(Exception):
        SolveRequest(task="x" * 10_001)

    request = SolveRequest(task="Tell me about AI")

    assert request.task == "Tell me about AI"
    assert request.human_approved is False


def test_solve_route_declares_dedicated_http_contracts():
    route = next(
        route
        for route in app.routes
        if route.path == "/api/v1/solve"
    )

    assert route.response_model is SolveResponse
    assert route.response_model_exclude_unset is True
    assert route.body_field is not None
    assert route.body_field.type_ is SolveRequest


def test_solve_response_status_schema_is_exhaustive():
    schema = SolveResponse.model_json_schema()
    assert set(schema["properties"]["status"]["enum"]) == {
        "awaiting_human_approval",
        "retrieval_unavailable",
        "grounding_unavailable",
        "execution_context_unavailable",
        "execution_failed",
        "orchestrated",
    }


def test_sparse_blocked_response_does_not_gain_null_fields():
    response = SolveResponse.model_validate(
        _approval_response()
    )

    serialized = response.model_dump(exclude_unset=True)

    assert serialized["status"] == "awaiting_human_approval"
    assert "execution" not in serialized
    assert "result" not in serialized
    assert "evaluation" not in serialized
    assert "quality_recovery" not in serialized
    assert "outcome" not in serialized


def test_response_preserves_extension_metadata():
    response = SolveResponse.model_validate(
        _approval_response(
            diagnostic={"source": "step173"},
        )
    )

    serialized = response.model_dump(exclude_unset=True)

    assert serialized["diagnostic"] == {
        "source": "step173",
    }


def test_response_reuses_step172_canonical_validation():
    malformed = _approval_response()
    malformed["trace"] = [
        {
            "stage": "approval",
            "status": "required",
            "timestamp": "not-a-timestamp",
        }
    ]

    with pytest.raises(
        ValueError,
        match="valid ISO-8601 timestamp",
    ):
        SolveResponse.model_validate(malformed)


def test_response_rejects_unknown_terminal_status():
    malformed = _approval_response()
    malformed["status"] = "unknown"

    with pytest.raises(
        ValueError,
        match="supported orchestration terminal status",
    ):
        SolveResponse.model_validate(malformed)


def test_response_rejects_status_specific_missing_fields():
    with pytest.raises(
        ValueError,
        match="execution_failed orchestration result missing fields",
    ):
        SolveResponse.model_validate(
            {
                "status": "execution_failed",
                "analysis": {},
                "routing": {},
                "approval": {},
                "trace": [],
            }
        )


def test_openapi_documents_solve_request_and_response_models():
    schema = app.openapi()
    operation = schema["paths"]["/api/v1/solve"]["post"]

    request_ref = (
        operation["requestBody"]["content"]
        ["application/json"]["schema"]["$ref"]
    )
    response_ref = (
        operation["responses"]["200"]["content"]
        ["application/json"]["schema"]["$ref"]
    )

    assert request_ref.endswith("/SolveRequest")
    assert response_ref.endswith("/SolveResponse")


def test_solve_response_model_keeps_common_fields_required():
    assert SolveResponse.model_fields["analysis"].is_required()
    assert SolveResponse.model_fields["routing"].is_required()
    assert SolveResponse.model_fields["approval"].is_required()
    assert SolveResponse.model_fields["trace"].is_required()
