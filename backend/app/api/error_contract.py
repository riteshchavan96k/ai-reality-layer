from typing import Any, Literal, TypeAlias

from fastapi.encoders import jsonable_encoder
from pydantic import BaseModel, ConfigDict, Field


class ValidationIssue(BaseModel):
    """Safe validation detail exposed to API clients."""

    model_config = ConfigDict(extra="forbid")

    type: str = Field(min_length=1)
    loc: list[str | int]
    msg: str = Field(min_length=1)
    ctx: dict[str, Any] | None = None


class ValidationErrorDetail(BaseModel):
    """Exact 422 error body."""

    model_config = ConfigDict(extra="forbid")

    code: Literal["validation_error"] = "validation_error"
    message: Literal["Request validation failed."] = (
        "Request validation failed."
    )
    details: list[ValidationIssue]


class ValidationErrorResponse(BaseModel):
    """Canonical request-validation error envelope."""

    model_config = ConfigDict(extra="forbid")

    status: Literal["error"] = "error"
    error: ValidationErrorDetail
    request_id: str | None = None


class InternalErrorDetail(BaseModel):
    """Exact safe 500 error body."""

    model_config = ConfigDict(extra="forbid")

    code: Literal["internal_error"] = "internal_error"
    message: Literal["An internal server error occurred."] = (
        "An internal server error occurred."
    )


class InternalErrorResponse(BaseModel):
    """Canonical internal-error envelope."""

    model_config = ConfigDict(extra="forbid")

    status: Literal["error"] = "error"
    error: InternalErrorDetail
    request_id: str | None = None


ApiErrorResponse: TypeAlias = (
    ValidationErrorResponse | InternalErrorResponse
)


def normalize_validation_issues(
    raw_errors: list[dict[str, Any]],
) -> list[ValidationIssue]:
    """Remove rejected input values while preserving useful validation metadata."""
    issues: list[ValidationIssue] = []

    for raw_error in raw_errors:
        if not isinstance(raw_error, dict):
            raise ValueError("validation error details must be mappings")

        raw_loc = raw_error.get("loc", [])
        if not isinstance(raw_loc, (list, tuple)):
            raw_loc = [raw_loc]

        loc: list[str | int] = []
        for item in raw_loc:
            if isinstance(item, bool):
                loc.append(str(item))
            elif isinstance(item, (str, int)):
                loc.append(item)
            else:
                loc.append(str(item))

        ctx = raw_error.get("ctx")
        safe_ctx = None
        if isinstance(ctx, dict):
            encoded_ctx = jsonable_encoder(ctx)
            if isinstance(encoded_ctx, dict):
                safe_ctx = encoded_ctx

        issues.append(
            ValidationIssue(
                type=str(raw_error.get("type") or "validation_error"),
                loc=loc,
                msg=str(
                    raw_error.get("msg")
                    or "Request validation failed."
                ),
                ctx=safe_ctx,
            )
        )

    return issues


def build_validation_error_response(
    raw_errors: list[dict[str, Any]],
    request_id: str | None,
) -> ValidationErrorResponse:
    return ValidationErrorResponse(
        error=ValidationErrorDetail(
            details=normalize_validation_issues(raw_errors),
        ),
        request_id=request_id,
    )


def build_internal_error_response(
    request_id: str | None,
) -> InternalErrorResponse:
    return InternalErrorResponse(
        error=InternalErrorDetail(),
        request_id=request_id,
    )


__all__ = [
    "ApiErrorResponse",
    "InternalErrorDetail",
    "InternalErrorResponse",
    "ValidationErrorDetail",
    "ValidationErrorResponse",
    "ValidationIssue",
    "build_internal_error_response",
    "build_validation_error_response",
    "normalize_validation_issues",
]
