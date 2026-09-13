from dataclasses import dataclass
from typing import Any


@dataclass(frozen=True)
class EvidenceNormalizationConsumptionResult:
    """Stable result contract for the evidence-normalization consumption decision."""

    status: str
    evidence_status: str
    usable: bool
    reason: str | None = None
    consumption_evaluated: bool = True

    def __post_init__(self) -> None:
        if self.status not in {"usable", "rejected"}:
            raise ValueError("status must be usable or rejected")
        if self.evidence_status not in {
            "completed", "not_required", "invalid_evidence", "unknown"
        }:
            raise ValueError("evidence_status must be a supported evidence status")
        if not isinstance(self.usable, bool):
            raise ValueError("usable must be a boolean")
        if not isinstance(self.consumption_evaluated, bool):
            raise ValueError("consumption_evaluated must be a boolean")
        if self.status == "usable" and not self.usable:
            raise ValueError("usable status requires usable=True")
        if self.status == "rejected" and self.usable:
            raise ValueError("rejected status requires usable=False")
        if self.reason is not None and (
            not isinstance(self.reason, str) or not self.reason.strip()
        ):
            raise ValueError("reason must be a nonempty string when provided")

    @classmethod
    def usable_result(cls, evidence_status: str) -> "EvidenceNormalizationConsumptionResult":
        return cls(status="usable", evidence_status=evidence_status, usable=True)

    @classmethod
    def rejected_result(
        cls,
        evidence_status: str,
        reason: str = "evidence_normalization_consumption_rejected",
    ) -> "EvidenceNormalizationConsumptionResult":
        return cls(
            status="rejected",
            evidence_status=evidence_status,
            usable=False,
            reason=reason,
        )

    def to_dict(self) -> dict[str, Any]:
        return {
            "status": self.status,
            "evidence_status": self.evidence_status,
            "usable": self.usable,
            "reason": self.reason,
            "consumption_evaluated": self.consumption_evaluated,
        }


__all__ = ["EvidenceNormalizationConsumptionResult"]
