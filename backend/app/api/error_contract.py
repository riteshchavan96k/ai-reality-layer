from typing import Any, Literal

from fastapi.encoders import jsonable_encoder
from pydantic import BaseModel, ConfigDict, Field, model_validator


class ValidationIssue(BaseModel):
    """Safe validation detail exposed to API clients."""

    model_config = ConfigDict(extra="forbid")

    type: str = Field(min_length=1)
    loc: list[str | int]
    msg: str = Field(min_length=1)
    ctx: dict[str, Any] | None = None


class ApiErrorDetail(BaseModel):
    """Canonical API error body."""

    model_config = ConfigDict(extra="forbid")

    code: Literal["validation_error", "internal_error"]
    message: str = Field(min_length=1)
    details: list[ValidationIssue] | None = None

    @model_validator(mode="after")
    def validate_details_by_code(self) -> "ApiErrorDetail":
        if self.code == "validation_error":
            if self.details is None:
                raise ValueError(
                    "validation_error must include validation details"
                )
        elif self.details is not None:
            raise ValueError(
                "internal_error must not expose validation details"
            )
        return self


class ApiErrorResponse(BaseModel):
    """Canonical HTTP error envelope for public API failures."""

    model_config = ConfigDict(extra="forbid")

    status: Literal["error"]
    error: ApiErrorDetail
    request_id: str | None = None


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
) -> ApiErrorResponse:
    return ApiErrorResponse(
        status="error",
        error=ApiErrorDetail(
            code="validation_error",
            message="Request validation failed.",
            details=normalize_validation_issues(raw_errors),
        ),
        request_id=request_id,
    )


def build_internal_error_response(
    request_id: str | None,
) -> ApiErrorResponse:
    return ApiErrorResponse(
        status="error",
        error=ApiErrorDetail(
            code="internal_error",
            message="An internal server error occurred.",
        ),
        request_id=request_id,
    )


__all__ = [
    "ApiErrorDetail",
    "ApiErrorResponse",
    "ValidationIssue",
    "build_internal_error_response",
    "build_validation_error_response",
    "normalize_validation_issues",
]
