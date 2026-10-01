import asyncio
import json
from types import SimpleNamespace
from uuid import UUID

import pytest
from fastapi.exceptions import RequestValidationError
from starlette.requests import Request
from starlette.responses import Response

from backend.app.api.errors import validation_exception_handler
from backend.app.api.request_id import (
    REQUEST_ID_HEADER,
    REQUEST_ID_MAX_LENGTH,
    RequestIdMiddleware,
    canonical_request_id,
    is_valid_request_id,
)
from backend.app.main import app


def _request_with_header(value: str | None) -> Request:
    headers = []
    if value is not None:
        headers.append(
            (
                REQUEST_ID_HEADER.lower().encode("ascii"),
                value.encode("latin-1", errors="ignore"),
            )
        )

    scope = {
        "type": "http",
        "asgi": {"version": "3.0"},
        "http_version": "1.1",
        "method": "GET",
        "scheme": "http",
        "path": "/health",
        "raw_path": b"/health",
        "query_string": b"",
        "headers": headers,
        "client": ("testclient", 12345),
        "server": ("testserver", 80),
        "root_path": "",
    }
    return Request(scope)


def _run_middleware(value: str | None):
    request = _request_with_header(value)
    middleware = RequestIdMiddleware(
        app=lambda scope, receive, send: None
    )

    async def call_next(inner_request):
        response = Response("ok")
        response.state_request_id = inner_request.state.request_id
        return response

    response = asyncio.run(
        middleware.dispatch(request, call_next)
    )
    return request, response


def _validation_exception():
    return RequestValidationError(
        [
            {
                "type": "string_too_short",
                "loc": ("body", "task"),
                "msg": "String should have at least 1 character",
                "input": "",
            }
        ]
    )


def test_valid_request_id_is_preserved_exactly():
    value = "client-1234.trace:abc_01"

    assert is_valid_request_id(value) is True
    assert canonical_request_id(value) == value


def test_maximum_length_request_id_is_valid():
    value = "a" * REQUEST_ID_MAX_LENGTH

    assert len(value) == 128
    assert is_valid_request_id(value) is True
    assert canonical_request_id(value) == value


@pytest.mark.parametrize(
    "value",
    [
        None,
        "",
        " leading-space",
        "trailing-space ",
        "contains space",
        "line\nbreak",
        "tab\tvalue",
        "é",
        "a" * (REQUEST_ID_MAX_LENGTH + 1),
        object(),
    ],
)
def test_invalid_request_ids_are_replaced_with_safe_uuid(value):
    result = canonical_request_id(value)

    assert result != value
    assert is_valid_request_id(result) is True
    assert str(UUID(result)) == result


def test_middleware_preserves_valid_client_request_id_in_state_and_response():
    request_id = "client-request-175"

    request, response = _run_middleware(request_id)

    assert request.state.request_id == request_id
    assert response.headers[REQUEST_ID_HEADER] == request_id
    assert response.state_request_id == request_id


def test_middleware_replaces_unsafe_client_request_id_consistently():
    unsafe = "unsafe request id"

    request, response = _run_middleware(unsafe)
    canonical = request.state.request_id

    assert canonical != unsafe
    assert is_valid_request_id(canonical)
    assert response.headers[REQUEST_ID_HEADER] == canonical
    assert response.state_request_id == canonical


def test_error_handler_does_not_reflect_invalid_request_state_id():
    request = SimpleNamespace(
        state=SimpleNamespace(
            request_id="unsafe request id",
        )
    )

    response = validation_exception_handler(
        request,
        _validation_exception(),
    )
    body = json.loads(response.body)

    assert body["request_id"] is None
    assert "unsafe request id" not in response.body.decode()


@pytest.mark.parametrize(
    ("path", "method", "response_codes"),
    [
        (
            "/health",
            "get",
            {"200", "500"},
        ),
        (
            "/api/v1/solve",
            "post",
            {"200", "422", "500"},
        ),
        (
            "/api/v1/reality-state",
            "post",
            {"200", "422", "500"},
        ),
    ],
)
def test_public_routes_document_request_id_parameter_and_response_headers(
    path,
    method,
    response_codes,
):
    schema = app.openapi()
    operation = schema["paths"][path][method]

    parameters = [
        parameter
        for parameter in operation["parameters"]
        if parameter["in"] == "header"
        and parameter["name"] == REQUEST_ID_HEADER
    ]

    assert len(parameters) == 1
    parameter = parameters[0]
    assert parameter["required"] is False
    assert parameter["schema"]["minLength"] == 1
    assert parameter["schema"]["maxLength"] == REQUEST_ID_MAX_LENGTH
    assert "pattern" in parameter["schema"]

    for code in response_codes:
        response = operation["responses"][code]
        assert REQUEST_ID_HEADER in response["headers"]
        header_schema = response["headers"][REQUEST_ID_HEADER]["schema"]
        assert header_schema["minLength"] == 1
        assert header_schema["maxLength"] == REQUEST_ID_MAX_LENGTH
        assert "pattern" in header_schema


def test_request_id_header_documentation_preserves_success_body_schemas():
    schema = app.openapi()

    solve_success = (
        schema["paths"]["/api/v1/solve"]["post"]
        ["responses"]["200"]
    )
    reality_success = (
        schema["paths"]["/api/v1/reality-state"]["post"]
        ["responses"]["200"]
    )

    assert (
        solve_success["content"]["application/json"]["schema"]["$ref"]
        .endswith("/SolveResponse")
    )
    assert (
        reality_success["content"]["application/json"]["schema"]["$ref"]
        .endswith("/RealityStateResponse")
    )


def test_request_id_header_documentation_preserves_error_body_schemas():
    schema = app.openapi()
    responses = (
        schema["paths"]["/api/v1/solve"]["post"]["responses"]
    )

    assert (
        responses["422"]["content"]["application/json"]["schema"]["$ref"]
        .endswith("/ValidationErrorResponse")
    )
    assert (
        responses["500"]["content"]["application/json"]["schema"]["$ref"]
        .endswith("/InternalErrorResponse")
    )


def test_health_does_not_gain_validation_error_response():
    schema = app.openapi()
    responses = schema["paths"]["/health"]["get"]["responses"]

    assert "422" not in responses
