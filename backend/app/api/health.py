from typing import Literal

from pydantic import BaseModel, ConfigDict, Field


SERVICE_NAME = "ai-reality-layer"
API_VERSION = "0.1.0"


class HealthResponse(BaseModel):
    """HTTP liveness response for the AI Reality Layer API process."""

    model_config = ConfigDict(extra="forbid")

    status: Literal["healthy"] = "healthy"
    service: Literal["ai-reality-layer"] = SERVICE_NAME
    version: str = Field(
        default=API_VERSION,
        pattern=r"^\d+\.\d+\.\d+$",
    )


def build_health_response() -> HealthResponse:
    """Build the canonical process-liveness response."""
    return HealthResponse(
        status="healthy",
        service=SERVICE_NAME,
        version=API_VERSION,
    )


__all__ = [
    "API_VERSION",
    "SERVICE_NAME",
    "HealthResponse",
    "build_health_response",
]
