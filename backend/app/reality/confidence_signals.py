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
        if self.status not in {"supported", "uncertain", "insufficient", "unavailable"}:
            raise ValueError("status must be supported, uncertain, insufficient, or unavailable")
        if not isinstance(self.evidence_usable, bool):
            raise ValueError("evidence_usable must be a boolean")
        if self.claim_coverage is not None and (
            not isinstance(self.claim_coverage, (int, float))
            or isinstance(self.claim_coverage, bool)
            or not 0 <= self.claim_coverage <= 1
        ):
            raise ValueError("claim_coverage must be between 0 and 1 or None")
        if self.freshness_status not in {"usable", "empty", "unavailable"}:
            raise ValueError("freshness_status is invalid")
        if not isinstance(self.conflict_count, int) or isinstance(self.conflict_count, bool) or self.conflict_count < 0:
            raise ValueError("conflict_count must be a non-negative integer")
        if not isinstance(self.signals, tuple) or any(not isinstance(x, str) or not x.strip() for x in self.signals):
            raise ValueError("signals must be a tuple of non-empty strings")
        if self.confidence_method != "deterministic_signal_aggregation":
            raise ValueError("confidence_method must be deterministic_signal_aggregation")
        if self.status == "unavailable" and (not isinstance(self.reason, str) or not self.reason.strip()):
            raise ValueError("unavailable result requires a reason")
        if self.status != "unavailable" and self.reason is not None:
            raise ValueError("non-unavailable result cannot contain a reason")

    @classmethod
    def validate(cls, raw_result: object) -> "RealityConfidenceSignalResult":
        """Validate or normalize a canonical confidence-signal result."""
        if isinstance(raw_result, cls):
            return raw_result
        if not isinstance(raw_result, dict):
            raise ValueError("confidence signal result must be a mapping or RealityConfidenceSignalResult")
        required = {
            "status",
            "evidence_usable",
            "claim_coverage",
            "freshness_status",
            "conflict_count",
            "signals",
            "confidence_method",
            "reason",
        }
        missing = sorted(required - set(raw_result))
        if missing:
            raise ValueError(f"missing required fields: {', '.join(missing)}")
        raw_signals = raw_result["signals"]
        if not isinstance(raw_signals, (list, tuple)):
            raise ValueError("signals must be a list or tuple")
        return cls(
            status=raw_result["status"],
            evidence_usable=raw_result["evidence_usable"],
            claim_coverage=raw_result["claim_coverage"],
            freshness_status=raw_result["freshness_status"],
            conflict_count=raw_result["conflict_count"],
            signals=tuple(raw_signals),
            confidence_method=raw_result["confidence_method"],
            reason=raw_result["reason"],
        )

    def to_dict(self) -> dict[str, Any]:
        return {
            "status": self.status,
            "evidence_usable": self.evidence_usable,
            "claim_coverage": self.claim_coverage,
            "freshness_status": self.freshness_status,
            "conflict_count": self.conflict_count,
            "signals": list(self.signals),
            "confidence_method": self.confidence_method,
            "reason": self.reason,
        }


__all__ = ["RealityConfidenceSignalResult"]
