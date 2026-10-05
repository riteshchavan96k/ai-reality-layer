from typing import Any, Literal
from math import isfinite

from pydantic import BaseModel, ConfigDict, Field, field_validator


class RealityStateRequest(BaseModel):
    """HTTP request contract for Reality State construction."""

    model_config = ConfigDict(extra="forbid")

    task: str = Field(min_length=1, max_length=10_000)
    freshness_max_age_seconds: float | int | None = None

    @field_validator("freshness_max_age_seconds", mode="before")
    @classmethod
    def validate_freshness_window(cls, value: object) -> object:
        if value is None:
            return None
        if not isinstance(value, (int, float)) or isinstance(value, bool):
            raise ValueError("freshness_max_age_seconds must be a positive finite number")
        try:
            valid = value > 0 and isfinite(value)
        except OverflowError:
            valid = False
        if not valid:
            raise ValueError("freshness_max_age_seconds must be a positive finite number")
        return value


class RealityStateResponse(BaseModel):
    """HTTP response contract for the canonical Reality State snapshot."""

    status: Literal["supported", "uncertain", "insufficient", "unavailable"]
    task: str
    evidence: dict[str, Any]
    claims: dict[str, Any]
    claim_evidence_linking: dict[str, Any]
    source_provenance: dict[str, Any]
    source_observation: dict[str, Any]
    freshness: dict[str, Any]
    conflicts: dict[str, Any]
    confidence_signals: dict[str, Any]
    assembly_method: Literal["deterministic_signal_snapshot"]
    reason: str | None = None


__all__ = ["RealityStateRequest", "RealityStateResponse"]
