from dataclasses import dataclass
from typing import Any


@dataclass(frozen=True)
class ClaimConflict:
    """A deterministic candidate conflict between two extracted claims."""

    claim_a: str
    claim_b: str
    source_refs_a: tuple[str, ...] = ()
    source_refs_b: tuple[str, ...] = ()
    conflict_method: str = "explicit_negation_pair"

    def __post_init__(self) -> None:
        for value, name in ((self.claim_a, "claim_a"), (self.claim_b, "claim_b")):
            if not isinstance(value, str) or not value.strip():
                raise ValueError(f"{name} must be a non-empty string")
        for refs, name in ((self.source_refs_a, "source_refs_a"), (self.source_refs_b, "source_refs_b")):
            if not isinstance(refs, tuple) or any(not isinstance(ref, str) or not ref.strip() for ref in refs):
                raise ValueError(f"{name} must be a tuple of non-empty strings")
        if self.claim_a.casefold() == self.claim_b.casefold():
            raise ValueError("conflicting claims must be distinct")
        if self.conflict_method != "explicit_negation_pair":
            raise ValueError("conflict_method must be explicit_negation_pair")

    def to_dict(self) -> dict[str, Any]:
        return {"claim_a": self.claim_a, "claim_b": self.claim_b, "source_refs_a": list(self.source_refs_a), "source_refs_b": list(self.source_refs_b), "conflict_method": self.conflict_method}


@dataclass(frozen=True)
class ClaimConflictResult:
    """Canonical result of deterministic candidate-conflict detection."""

    status: str
    conflicts: tuple[ClaimConflict, ...] = ()
    claim_count: int = 0
    conflict_count: int = 0
    detection_executed: bool = True
    reason: str | None = None

    def __post_init__(self) -> None:
        if self.status not in {"usable", "empty", "unavailable"}:
            raise ValueError("status must be usable, empty, or unavailable")
        if not isinstance(self.conflicts, tuple) or any(not isinstance(item, ClaimConflict) for item in self.conflicts):
            raise ValueError("conflicts must be a tuple of ClaimConflict values")
        if self.claim_count < 0 or self.conflict_count < 0:
            raise ValueError("counts must be non-negative")
        if self.conflict_count != len(self.conflicts):
            raise ValueError("conflict_count must match conflicts")
        if not isinstance(self.detection_executed, bool):
            raise ValueError("detection_executed must be a boolean")
        if self.status == "usable" and not self.conflicts:
            raise ValueError("usable conflict result requires conflicts")
        if self.status in {"empty", "unavailable"} and self.conflicts:
            raise ValueError(f"{self.status} conflict result cannot contain conflicts")
        if self.status == "unavailable" and (not isinstance(self.reason, str) or not self.reason.strip()):
            raise ValueError("unavailable conflict result requires a reason")
        if self.status != "unavailable" and self.reason is not None:
            raise ValueError("usable or empty conflict result cannot contain a reason")

    @classmethod
    def usable_result(cls, conflicts: tuple[ClaimConflict, ...], claim_count: int) -> "ClaimConflictResult":
        return cls("usable", conflicts=conflicts, claim_count=claim_count, conflict_count=len(conflicts))

    @classmethod
    def empty_result(cls, claim_count: int = 0) -> "ClaimConflictResult":
        return cls("empty", claim_count=claim_count)

    @classmethod
    def unavailable_result(cls, reason: str, claim_count: int = 0) -> "ClaimConflictResult":
        return cls("unavailable", claim_count=claim_count, reason=reason)

    def to_dict(self) -> dict[str, Any]:
        return {"status": self.status, "conflicts": [item.to_dict() for item in self.conflicts], "conflict_count": self.conflict_count, "claim_count": self.claim_count, "detection_executed": self.detection_executed, "reason": self.reason}


__all__ = ["ClaimConflict", "ClaimConflictResult"]
