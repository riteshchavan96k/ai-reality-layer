from dataclasses import dataclass
from typing import Any

@dataclass(frozen=True)
class RealityConfidenceSignalResult:
    """Canonical non-probabilistic confidence signal profile."""
    status: str
    evidence_usable: bool
    claim_coverage: float | None
    freshness_status: str
    conflict_count: int
    signals: tuple[str, ...] = ()
    confidence_method: str = "deterministic_signal_aggregation"
    reason: str | None = None
    def __post_init__(self) -> None:
        if self.status not in {"supported", "uncertain", "insufficient", "unavailable"}: raise ValueError("status must be supported, uncertain, insufficient, or unavailable")
        if not isinstance(self.evidence_usable, bool): raise ValueError("evidence_usable must be a boolean")
        if self.claim_coverage is not None and (not isinstance(self.claim_coverage, (int, float)) or not 0 <= self.claim_coverage <= 1): raise ValueError("claim_coverage must be between 0 and 1 or None")
        if self.freshness_status not in {"usable", "empty", "unavailable"}: raise ValueError("freshness_status is invalid")
        if not isinstance(self.conflict_count, int) or self.conflict_count < 0: raise ValueError("conflict_count must be a non-negative integer")
        if not isinstance(self.signals, tuple) or any(not isinstance(x, str) or not x.strip() for x in self.signals): raise ValueError("signals must be a tuple of non-empty strings")
        if self.confidence_method != "deterministic_signal_aggregation": raise ValueError("confidence_method must be deterministic_signal_aggregation")
        if self.status == "unavailable" and (not isinstance(self.reason, str) or not self.reason.strip()): raise ValueError("unavailable result requires a reason")
        if self.status != "unavailable" and self.reason is not None: raise ValueError("non-unavailable result cannot contain a reason")
    def to_dict(self) -> dict[str, Any]:
        return {"status": self.status, "evidence_usable": self.evidence_usable, "claim_coverage": self.claim_coverage, "freshness_status": self.freshness_status, "conflict_count": self.conflict_count, "signals": list(self.signals), "confidence_method": self.confidence_method, "reason": self.reason}

__all__ = ["RealityConfidenceSignalResult"]
