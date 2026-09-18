from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, Field


class RealityStateRequest(BaseModel):
    """HTTP request contract for Reality State construction."""

    model_config = ConfigDict(extra="forbid")

    task: str = Field(min_length=1, max_length=10_000)


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
