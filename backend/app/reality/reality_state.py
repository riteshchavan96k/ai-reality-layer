from dataclasses import dataclass
from typing import Any


_ALLOWED_STATUSES = {"supported", "uncertain", "insufficient", "unavailable"}
_REQUIRED_SNAPSHOT_FIELDS = (
    "evidence",
    "claims",
    "claim_evidence_linking",
    "source_provenance",
    "source_observation",
    "freshness",
    "conflicts",
    "confidence_signals",
)


@dataclass(frozen=True)
class RealityState:
    """Canonical immutable snapshot of the evidence-backed reality signals."""

    status: str
    task: str
    evidence: dict[str, Any]
    claims: dict[str, Any]
    claim_evidence_linking: dict[str, Any]
    source_provenance: dict[str, Any]
    source_observation: dict[str, Any]
    freshness: dict[str, Any]
    conflicts: dict[str, Any]
    confidence_signals: dict[str, Any]
    assembly_method: str = "deterministic_signal_snapshot"
    reason: str | None = None

    def __post_init__(self) -> None:
        if self.status not in _ALLOWED_STATUSES:
            raise ValueError("invalid reality state status")
        if not isinstance(self.task, str) or not self.task.strip():
            raise ValueError("task must be a non-empty string")
        for name in _REQUIRED_SNAPSHOT_FIELDS:
            value = getattr(self, name)
            if not isinstance(value, dict):
                raise ValueError(f"{name} must be a dictionary")
        if self.assembly_method != "deterministic_signal_snapshot":
            raise ValueError("invalid assembly method")
        if self.status == "unavailable" and (not isinstance(self.reason, str) or not self.reason.strip()):
            raise ValueError("unavailable state requires a reason")
        if self.status != "unavailable" and self.reason is not None:
            raise ValueError("non-unavailable state cannot contain a reason")

    @classmethod
    def validate(cls, raw_state: object) -> "RealityState":
        """Validate or normalize a canonical RealityState value."""
        if isinstance(raw_state, cls):
            return raw_state
        if not isinstance(raw_state, dict):
            raise ValueError("reality state must be a mapping or RealityState")

        required = {"status", "task", *_REQUIRED_SNAPSHOT_FIELDS, "assembly_method", "reason"}
        missing = sorted(required - set(raw_state))
        if missing:
            raise ValueError(f"missing required fields: {', '.join(missing)}")

        return cls(
            status=raw_state["status"],
            task=raw_state["task"],
            evidence=raw_state["evidence"],
            claims=raw_state["claims"],
            claim_evidence_linking=raw_state["claim_evidence_linking"],
            source_provenance=raw_state["source_provenance"],
            source_observation=raw_state["source_observation"],
            freshness=raw_state["freshness"],
            conflicts=raw_state["conflicts"],
            confidence_signals=raw_state["confidence_signals"],
            assembly_method=raw_state["assembly_method"],
            reason=raw_state["reason"],
        )

    def to_dict(self) -> dict[str, Any]:
        return {
            "status": self.status,
            "task": self.task,
            "evidence": self.evidence,
            "claims": self.claims,
            "claim_evidence_linking": self.claim_evidence_linking,
            "source_provenance": self.source_provenance,
            "source_observation": self.source_observation,
            "freshness": self.freshness,
            "conflicts": self.conflicts,
            "confidence_signals": self.confidence_signals,
            "assembly_method": self.assembly_method,
            "reason": self.reason,
        }


__all__ = ["RealityState"]
