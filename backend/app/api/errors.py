from typing import Any

from fastapi import Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse


def validation_exception_handler(
    request: Request, exc: RequestValidationError
) -> JSONResponse:
    return JSONResponse(
        status_code=422,
        content={
            "status": "error",
            "error": {
                "code": "validation_error",
                "message": "Request validation failed.",
                "details": exc.errors(),
            },
            "request_id": getattr(request.state, "request_id", None),
        },
    )


def unhandled_exception_handler(
    request: Request, exc: Exception
) -> JSONResponse:
    return JSONResponse(
        status_code=500,
        content={
            "status": "error",
            "error": {
                "code": "internal_error",
                "message": "An internal server error occurred.",
            },
            "request_id": getattr(request.state, "request_id", None),
        },
    )
