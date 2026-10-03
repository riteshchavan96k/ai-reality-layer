from fastapi import FastAPI
from fastapi.exceptions import RequestValidationError
from backend.app.api.error_contract import (
    InternalErrorResponse,
    ValidationErrorResponse,
)
from backend.app.api.errors import (
    unhandled_exception_handler,
    validation_exception_handler,
)
from backend.app.api.evidence_reality_state import EvidenceRealityStateRequest
from backend.app.api.health import (
    API_VERSION,
    HealthResponse,
    build_health_response,
)
from backend.app.api.request_id import (
    REQUEST_ID_HEADER,
    REQUEST_ID_OPENAPI_PARAMETER,
    REQUEST_ID_OPENAPI_RESPONSE_HEADER,
    RequestIdMiddleware,
)
from backend.app.api.reality_state import RealityStateRequest, RealityStateResponse
from backend.app.api.solve import SolveRequest, SolveResponse
from backend.app.services.solve_service import process_task
from backend.app.orchestrator.orchestrator import (
    build_reality_state,
    build_reality_state_from_evidence,
)


app = FastAPI(
    title="AI Reality Layer API",
    version=API_VERSION,
    description="Production-oriented API surface for AI Reality Layer orchestration.",
)

app.add_middleware(RequestIdMiddleware)
app.add_exception_handler(RequestValidationError, validation_exception_handler)
app.add_exception_handler(Exception, unhandled_exception_handler)


_REQUEST_ID_RESPONSE_HEADERS = {
    REQUEST_ID_HEADER: REQUEST_ID_OPENAPI_RESPONSE_HEADER,
}

_REQUEST_ID_OPENAPI_EXTRA = {
    "parameters": [REQUEST_ID_OPENAPI_PARAMETER],
}

_VALIDATION_AND_INTERNAL_ERROR_RESPONSES = {
    200: {
        "headers": _REQUEST_ID_RESPONSE_HEADERS,
    },
    422: {
        "model": ValidationErrorResponse,
        "description": "Request validation failed.",
        "headers": _REQUEST_ID_RESPONSE_HEADERS,
    },
    500: {
        "model": InternalErrorResponse,
        "description": "An internal server error occurred.",
        "headers": _REQUEST_ID_RESPONSE_HEADERS,
    },
}

_HEALTH_RESPONSES = {
    200: {
        "headers": _REQUEST_ID_RESPONSE_HEADERS,
    },
    500: {
        "model": InternalErrorResponse,
        "description": "An internal server error occurred.",
        "headers": _REQUEST_ID_RESPONSE_HEADERS,
    },
}


@app.get(
    "/health",
    response_model=HealthResponse,
    responses=_HEALTH_RESPONSES,
    openapi_extra=_REQUEST_ID_OPENAPI_EXTRA,
)
def health_check():
    return build_health_response()


@app.post(
    "/api/v1/solve",
    response_model=SolveResponse,
    response_model_exclude_unset=True,
    responses=_VALIDATION_AND_INTERNAL_ERROR_RESPONSES,
    openapi_extra=_REQUEST_ID_OPENAPI_EXTRA,
)
def solve(request: SolveRequest):
    return process_task(request.task, human_approved=request.human_approved)




@app.post(
    "/api/v1/reality-state/evidence",
    response_model=RealityStateResponse,
    responses=_VALIDATION_AND_INTERNAL_ERROR_RESPONSES,
    openapi_extra=_REQUEST_ID_OPENAPI_EXTRA,
)
def reality_state_from_evidence(request: EvidenceRealityStateRequest):
    """Build a canonical Reality State from caller-supplied source-scoped evidence."""
    return build_reality_state_from_evidence(
        request.task,
        [document.model_dump() for document in request.documents],
    )

@app.post(
    "/api/v1/reality-state",
    response_model=RealityStateResponse,
    responses=_VALIDATION_AND_INTERNAL_ERROR_RESPONSES,
    openapi_extra=_REQUEST_ID_OPENAPI_EXTRA,
)
def reality_state(request: RealityStateRequest):
    """Return the canonical evidence-backed Reality State without a model execution request."""
    reality_state = build_reality_state(request.task)
    if reality_state is None:
        return {
            "status": "unavailable",
            "task": request.task,
            "reason": "reality_state_not_available",
        }
    return reality_state
