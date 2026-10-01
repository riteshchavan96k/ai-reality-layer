import json
from types import SimpleNamespace

import pytest
from fastapi.exceptions import RequestValidationError

from backend.app.api.error_contract import (
    InternalErrorResponse,
    ValidationErrorResponse,
    build_internal_error_response,
    build_validation_error_response,
)
from backend.app.api.errors import (
    unhandled_exception_handler,
    validation_exception_handler,
)
from backend.app.main import app


def _request(request_id="request-174"):
    return SimpleNamespace(
        state=SimpleNamespace(request_id=request_id)
    )


def _validation_exception(secret_input="super-secret-value"):
    return RequestValidationError(
        [
            {
                "type": "string_too_short",
                "loc": ("body", "task"),
                "msg": "String should have at least 1 character",
                "input": secret_input,
                "ctx": {
                    "min_length": 1,
                    "error": RuntimeError("private-validator-detail"),
                },
            }
        ]
    )


def test_validation_error_builder_returns_exact_contract():
    payload = build_validation_error_response(
        _validation_exception().errors(),
        "request-174",
    )

    assert isinstance(payload, ValidationErrorResponse)
    value = payload.model_dump(mode="json", exclude_none=True)

    assert value["status"] == "error"
    assert value["error"]["code"] == "validation_error"
    assert value["error"]["message"] == "Request validation failed."
    assert value["request_id"] == "request-174"
    assert value["error"]["details"] == [
        {
            "type": "string_too_short",
            "loc": ["body", "task"],
            "msg": "String should have at least 1 character",
        }
    ]


def test_validation_error_contract_does_not_echo_rejected_input_or_raw_context():
    secret = "never-return-this-input"
    payload = build_validation_error_response(
        _validation_exception(secret).errors(),
        "request-174",
    )
    encoded = json.dumps(
        payload.model_dump(mode="json", exclude_none=True)
    )

    assert secret not in encoded
    assert "private-validator-detail" not in encoded
    assert '"input"' not in encoded
    assert '"ctx"' not in encoded


def test_validation_handler_returns_canonical_422_and_request_id():
    response = validation_exception_handler(
        _request(),
        _validation_exception(),
    )
    body = json.loads(response.body)

    assert response.status_code == 422
    assert ValidationErrorResponse.model_validate(body)
    assert body["request_id"] == "request-174"
    assert body["error"]["code"] == "validation_error"


def test_validation_handler_keeps_null_request_id_field_for_legacy_shape():
    response = validation_exception_handler(
        _request(None),
        _validation_exception(),
    )
    body = json.loads(response.body)

    assert "request_id" in body
    assert body["request_id"] is None


def test_internal_error_builder_has_no_details_surface():
    payload = build_internal_error_response("request-174")

    assert isinstance(payload, InternalErrorResponse)
    value = payload.model_dump(mode="json")

    assert value == {
        "status": "error",
        "error": {
            "code": "internal_error",
            "message": "An internal server error occurred.",
        },
        "request_id": "request-174",
    }


def test_internal_error_handler_never_exposes_exception_text():
    secret = "database-password-is-secret"
    response = unhandled_exception_handler(
        _request(),
        RuntimeError(secret),
    )
    body = json.loads(response.body)
    encoded = json.dumps(body)

    assert response.status_code == 500
    assert InternalErrorResponse.model_validate(body)
    assert secret not in encoded
    assert body["error"] == {
        "code": "internal_error",
        "message": "An internal server error occurred.",
    }


@pytest.mark.parametrize(
    ("path", "method"),
    [
        ("/api/v1/solve", "post"),
        ("/api/v1/reality-state", "post"),
    ],
)
def test_post_endpoints_document_canonical_422_and_500_models(path, method):
    schema = app.openapi()
    responses = schema["paths"][path][method]["responses"]

    validation_ref = (
        responses["422"]["content"]["application/json"]["schema"]["$ref"]
    )
    internal_ref = (
        responses["500"]["content"]["application/json"]["schema"]["$ref"]
    )

    assert validation_ref.endswith("/ValidationErrorResponse")
    assert internal_ref.endswith("/InternalErrorResponse")


def test_health_endpoint_documents_canonical_500_model():
    schema = app.openapi()
    responses = schema["paths"]["/health"]["get"]["responses"]

    internal_ref = (
        responses["500"]["content"]["application/json"]["schema"]["$ref"]
    )

    assert internal_ref.endswith("/InternalErrorResponse")
    assert "422" not in responses


def test_openapi_validation_error_schema_excludes_rejected_input_fields():
    schema = app.openapi()
    issue_schema = schema["components"]["schemas"]["ValidationIssue"]

    assert set(issue_schema["properties"]) == {
        "type",
        "loc",
        "msg",
    }


def test_error_contracts_forbid_unknown_fields():
    with pytest.raises(Exception):
        InternalErrorResponse.model_validate(
            {
                "status": "error",
                "error": {
                    "code": "internal_error",
                    "message": "An internal server error occurred.",
                },
                "request_id": "request-174",
                "unexpected": True,
            }
        )

    with pytest.raises(Exception):
        ValidationErrorResponse.model_validate(
            {
                "status": "error",
                "error": {
                    "code": "validation_error",
                    "message": "Request validation failed.",
                    "details": [],
                    "unexpected": True,
                },
                "request_id": "request-174",
            }
        )
