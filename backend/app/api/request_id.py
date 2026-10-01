import re
from typing import Any
from uuid import uuid4

from fastapi import Request
from starlette.middleware.base import BaseHTTPMiddleware


REQUEST_ID_HEADER = "X-Request-ID"
REQUEST_ID_MAX_LENGTH = 128
_REQUEST_ID_PATTERN = re.compile(
    rf"^[A-Za-z0-9][A-Za-z0-9._:-]{{0,{REQUEST_ID_MAX_LENGTH - 1}}}$"
)

REQUEST_ID_OPENAPI_PARAMETER: dict[str, Any] = {
    "name": REQUEST_ID_HEADER,
    "in": "header",
    "required": False,
    "description": (
        "Optional client correlation ID. Values must be 1-128 ASCII "
        "characters using letters, digits, '.', '_', ':', or '-'. "
        "Missing or invalid values are replaced with a generated UUID."
    ),
    "schema": {
        "type": "string",
        "minLength": 1,
        "maxLength": REQUEST_ID_MAX_LENGTH,
        "pattern": _REQUEST_ID_PATTERN.pattern,
    },
}

REQUEST_ID_OPENAPI_RESPONSE_HEADER: dict[str, Any] = {
    "description": (
        "Canonical request correlation ID used for this response."
    ),
    "schema": {
        "type": "string",
        "minLength": 1,
        "maxLength": REQUEST_ID_MAX_LENGTH,
        "pattern": _REQUEST_ID_PATTERN.pattern,
    },
}


def is_valid_request_id(value: object) -> bool:
    """Return whether a value is safe to reuse as a public correlation ID."""
    return (
        isinstance(value, str)
        and len(value) <= REQUEST_ID_MAX_LENGTH
        and _REQUEST_ID_PATTERN.fullmatch(value) is not None
    )


def canonical_request_id(value: object) -> str:
    """Preserve a safe caller ID or replace it with a generated UUID."""
    if is_valid_request_id(value):
        return value
    return str(uuid4())


class RequestIdMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        request_id = canonical_request_id(
            request.headers.get(REQUEST_ID_HEADER)
        )
        request.state.request_id = request_id

        response = await call_next(request)
        response.headers[REQUEST_ID_HEADER] = request_id
        return response


__all__ = [
    "REQUEST_ID_HEADER",
    "REQUEST_ID_MAX_LENGTH",
    "REQUEST_ID_OPENAPI_PARAMETER",
    "REQUEST_ID_OPENAPI_RESPONSE_HEADER",
    "RequestIdMiddleware",
    "canonical_request_id",
    "is_valid_request_id",
]
