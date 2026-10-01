from fastapi import Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse

from backend.app.api.error_contract import (
    ApiErrorResponse,
    build_internal_error_response,
    build_validation_error_response,
)


def _request_id(request: Request) -> str | None:
    value = getattr(request.state, "request_id", None)
    return value if isinstance(value, str) and value else None


def _error_content(payload: ApiErrorResponse) -> dict:
    content = payload.model_dump(
        mode="json",
        exclude_none=True,
    )
    content["request_id"] = payload.request_id
    return content


def validation_exception_handler(
    request: Request,
    exc: RequestValidationError,
) -> JSONResponse:
    payload = build_validation_error_response(
        exc.errors(),
        _request_id(request),
    )
    return JSONResponse(
        status_code=422,
        content=_error_content(payload),
    )


def unhandled_exception_handler(
    request: Request,
    exc: Exception,
) -> JSONResponse:
    del exc
    payload = build_internal_error_response(
        _request_id(request),
    )
    return JSONResponse(
        status_code=500,
        content=_error_content(payload),
    )


__all__ = [
    "unhandled_exception_handler",
    "validation_exception_handler",
]
