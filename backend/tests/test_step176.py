import inspect

import pytest

from backend.app.api.health import (
    API_VERSION,
    SERVICE_NAME,
    HealthResponse,
    build_health_response,
)
from backend.app.main import app, health_check


def test_health_response_contract_is_exact_and_strict():
    assert set(HealthResponse.model_fields) == {
        "status",
        "service",
        "version",
    }

    response = HealthResponse()

    assert response.model_dump() == {
        "status": "healthy",
        "service": "ai-reality-layer",
        "version": "0.1.0",
    }


def test_health_response_rejects_invalid_status_service_version_and_extra_fields():
    with pytest.raises(Exception):
        HealthResponse(status="unhealthy")

    with pytest.raises(Exception):
        HealthResponse(service="another-service")

    with pytest.raises(Exception):
        HealthResponse(version="version-one")

    with pytest.raises(Exception):
        HealthResponse(unexpected=True)


def test_health_builder_uses_canonical_service_and_version_metadata():
    response = build_health_response()

    assert isinstance(response, HealthResponse)
    assert response.status == "healthy"
    assert response.service == SERVICE_NAME
    assert response.version == API_VERSION


def test_fastapi_metadata_and_health_version_share_one_version_source():
    response = build_health_response()

    assert app.version == API_VERSION
    assert response.version == app.version


def test_health_route_declares_canonical_success_model():
    route = next(
        route
        for route in app.routes
        if route.path == "/health"
    )

    assert route.response_model is HealthResponse


def test_health_handler_returns_typed_liveness_response():
    response = health_check()

    assert isinstance(response, HealthResponse)
    assert response.model_dump() == {
        "status": "healthy",
        "service": SERVICE_NAME,
        "version": API_VERSION,
    }


def test_health_handler_remains_liveness_only():
    source = inspect.getsource(health_check)

    assert "build_health_response()" in source
    assert "process_task" not in source
    assert "build_reality_state" not in source
    assert "retrieval" not in source.lower()
    assert "provider" not in source.lower()


def test_health_module_has_no_runtime_system_dependencies():
    import backend.app.api.health as health_module

    source = inspect.getsource(health_module)

    assert "backend.app.execution" not in source
    assert "backend.app.orchestrator" not in source
    assert "backend.app.retrieval" not in source
    assert "httpx" not in source
    assert "requests" not in source


def test_openapi_documents_health_success_and_internal_error_models():
    schema = app.openapi()
    responses = schema["paths"]["/health"]["get"]["responses"]

    success_ref = (
        responses["200"]["content"]["application/json"]["schema"]["$ref"]
    )
    internal_ref = (
        responses["500"]["content"]["application/json"]["schema"]["$ref"]
    )

    assert success_ref.endswith("/HealthResponse")
    assert internal_ref.endswith("/InternalErrorResponse")
    assert "422" not in responses


def test_openapi_health_schema_is_exact():
    schema = app.openapi()
    health_schema = schema["components"]["schemas"]["HealthResponse"]

    assert set(health_schema["properties"]) == {
        "status",
        "service",
        "version",
    }
    assert health_schema["additionalProperties"] is False

    status_schema = health_schema["properties"]["status"]
    service_schema = health_schema["properties"]["service"]
    version_schema = health_schema["properties"]["version"]

    assert status_schema.get("const") == "healthy"
    assert service_schema.get("const") == SERVICE_NAME
    assert version_schema["pattern"] == r"^\d+\.\d+\.\d+$"


def test_health_openapi_preserves_request_id_contract():
    schema = app.openapi()
    operation = schema["paths"]["/health"]["get"]

    parameters = [
        parameter
        for parameter in operation["parameters"]
        if parameter["in"] == "header"
        and parameter["name"] == "X-Request-ID"
    ]

    assert len(parameters) == 1
    assert "X-Request-ID" in operation["responses"]["200"]["headers"]
    assert "X-Request-ID" in operation["responses"]["500"]["headers"]
