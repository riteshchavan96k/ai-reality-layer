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
from backend.app.api.request_id import RequestIdMiddleware
from backend.app.api.reality_state import RealityStateRequest, RealityStateResponse
from backend.app.api.solve import SolveRequest, SolveResponse
from backend.app.services.solve_service import process_task
from backend.app.orchestrator.orchestrator import build_reality_state


app = FastAPI(
    title="AI Reality Layer API",
    version="0.1.0",
    description="Production-oriented API surface for AI Reality Layer orchestration.",
)

app.add_middleware(RequestIdMiddleware)
app.add_exception_handler(RequestValidationError, validation_exception_handler)
app.add_exception_handler(Exception, unhandled_exception_handler)


_VALIDATION_AND_INTERNAL_ERROR_RESPONSES = {
    422: {
        "model": ValidationErrorResponse,
        "description": "Request validation failed.",
    },
    500: {
        "model": InternalErrorResponse,
        "description": "An internal server error occurred.",
    },
}

_INTERNAL_ERROR_RESPONSE = {
    500: {
        "model": InternalErrorResponse,
        "description": "An internal server error occurred.",
    },
}


@app.get("/health", responses=_INTERNAL_ERROR_RESPONSE)
def health_check():
    return {
        "status": "healthy",
        "service": "ai-reality-layer",
        "version": "0.1.0",
    }


@app.post(
    "/api/v1/solve",
    response_model=SolveResponse,
    response_model_exclude_unset=True,
    responses=_VALIDATION_AND_INTERNAL_ERROR_RESPONSES,
)
def solve(request: SolveRequest):
    return process_task(request.task, human_approved=request.human_approved)


@app.post(
    "/api/v1/reality-state",
    response_model=RealityStateResponse,
    responses=_VALIDATION_AND_INTERNAL_ERROR_RESPONSES,
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
