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
from backend.app.api.original_source_claim import (
    OriginalSourceClaimRequest,
    OriginalSourceClaimResponse,
)
from backend.app.services.original_source_claim_service import verify_original_source_claim
from backend.app.api.original_source_answer import BoundedOriginalSourceAnswerResponse
from backend.app.services.original_source_answer_service import answer_original_source_claim
from backend.app.api.two_origin_answer import TwoOriginAnswerRequest, TwoOriginAnswerResponse
from backend.app.services.two_origin_answer_service import answer_two_distinct_https_origins
from backend.app.api.temporal_timeline import TemporalTimelineRequest, TemporalTimelineResponse
from backend.app.services.temporal_timeline_service import historical_timeline_readonly
from backend.app.api.pilot_auth import PilotAccessMiddleware
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
from backend.app.reality.reality_verification import RealityVerification


app = FastAPI(
    title="AI Reality Layer API",
    version=API_VERSION,
    description="Production-oriented API surface for AI Reality Layer orchestration.",
)

app.add_middleware(PilotAccessMiddleware)
# Request ID runs outermost, including on denied authentication responses.
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
    "/api/v1/reality-state/answer/compare",
    response_model=TwoOriginAnswerResponse,
    responses=_VALIDATION_AND_INTERNAL_ERROR_RESPONSES,
    openapi_extra=_REQUEST_ID_OPENAPI_EXTRA,
)
def two_origin_bounded_answer(request: TwoOriginAnswerRequest):
    """Return separately cited, bounded observations of the same claim from two HTTPS hosts."""
    return answer_two_distinct_https_origins(request)


@app.post(
    "/api/v1/reality-state/timeline",
    response_model=TemporalTimelineResponse,
    responses=_VALIDATION_AND_INTERNAL_ERROR_RESPONSES,
    openapi_extra=_REQUEST_ID_OPENAPI_EXTRA,
)
def original_source_historical_timeline(request: TemporalTimelineRequest):
    """Pilot-only, opt-in historical evidence read with no HTTPS or DB writes."""
    return historical_timeline_readonly(request)


@app.post(
    "/api/v1/reality-state/answer",
    response_model=BoundedOriginalSourceAnswerResponse,
    responses=_VALIDATION_AND_INTERNAL_ERROR_RESPONSES,
    openapi_extra=_REQUEST_ID_OPENAPI_EXTRA,
)
def original_source_bounded_answer(request: OriginalSourceClaimRequest):
    """One authenticated approved original-source observation, cited or abstained."""
    return answer_original_source_claim(request)


@app.post(
    "/api/v1/reality-state/claim",
    response_model=OriginalSourceClaimResponse,
    responses=_VALIDATION_AND_INTERNAL_ERROR_RESPONSES,
    openapi_extra=_REQUEST_ID_OPENAPI_EXTRA,
)
def reality_state_from_original_source_claim(request: OriginalSourceClaimRequest):
    """Verify one claim from a server-observed, operator-allowlisted source."""
    return verify_original_source_claim(request)


@app.post(
    "/api/v1/reality-state/evidence",
    response_model=RealityStateResponse,
    responses=_VALIDATION_AND_INTERNAL_ERROR_RESPONSES,
    openapi_extra=_REQUEST_ID_OPENAPI_EXTRA,
)
def reality_state_from_evidence(request: EvidenceRealityStateRequest):
    """Build a canonical Reality State from caller-supplied source-scoped evidence."""
    documents = [document.model_dump() for document in request.documents]
    if request.require_claim_alignment:
        return build_reality_state_from_evidence(
            request.task,
            documents,
            freshness_max_age_seconds=request.freshness_max_age_seconds,
            entity=request.entity,
            require_independent_source_text_match=True,
            require_claim_alignment=True,
            claim_text=request.claim_text,
        )
    if request.require_independent_source_text_match:
        return build_reality_state_from_evidence(
            request.task,
            documents,
            freshness_max_age_seconds=request.freshness_max_age_seconds,
            entity=request.entity,
            require_independent_source_text_match=True,
        )
    if request.entity is None:
        return build_reality_state_from_evidence(
            request.task,
            documents,
            freshness_max_age_seconds=request.freshness_max_age_seconds,
        )
    return build_reality_state_from_evidence(
        request.task,
        documents,
        freshness_max_age_seconds=request.freshness_max_age_seconds,
        entity=request.entity,
    )

@app.post(
    "/api/v1/reality-state",
    response_model=RealityStateResponse,
    responses=_VALIDATION_AND_INTERNAL_ERROR_RESPONSES,
    openapi_extra=_REQUEST_ID_OPENAPI_EXTRA,
)
def reality_state(request: RealityStateRequest):
    """Return the canonical evidence-backed Reality State without a model execution request."""
    if request.freshness_max_age_seconds is None:
        if request.entity is None:
            reality_state = build_reality_state(request.task)
        else:
            reality_state = build_reality_state(
                request.task,
                entity=request.entity,
            )
    elif request.entity is None:
        reality_state = build_reality_state(
            request.task,
            freshness_max_age_seconds=request.freshness_max_age_seconds,
        )
    else:
        reality_state = build_reality_state(
            request.task,
            freshness_max_age_seconds=request.freshness_max_age_seconds,
            entity=request.entity,
        )
    if reality_state is None:
        return {
            "status": "unavailable",
            "task": request.task,
            "entity": {
                "status": "specified" if request.entity is not None else "unspecified",
                "name": request.entity,
                "identification_method": (
                    "explicit_input" if request.entity is not None else "not_provided"
                ),
            },
            "verification": RealityVerification.not_completed(
                "reality_state_not_available"
            ).to_dict(),
            "evidence": {},
            "claims": {},
            "claim_evidence_linking": {},
            "source_provenance": {},
            "source_observation": {},
            "freshness": {},
            "conflicts": {},
            "confidence_signals": {},
            "assembly_method": "deterministic_signal_snapshot",
            "reason": "reality_state_not_available",
        }
    return reality_state
