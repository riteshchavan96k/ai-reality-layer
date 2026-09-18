from dataclasses import dataclass
from typing import Any


@dataclass(frozen=True)
class ClaimEvidenceLink:
    """A provenance relationship between a candidate claim and an evidence source."""

    claim_text: str
    source_ref: str
    relationship: str = "derived_from"
    linking_method: str = "source_ref_intersection"

    def __post_init__(self) -> None:
        if not isinstance(self.claim_text, str) or not self.claim_text.strip():
            raise ValueError("claim_text must be a non-empty string")
        if not isinstance(self.source_ref, str) or not self.source_ref.strip():
            raise ValueError("source_ref must be a non-empty string")
        if self.relationship != "derived_from":
            raise ValueError("relationship must be derived_from")
        if not isinstance(self.linking_method, str) or not self.linking_method.strip():
            raise ValueError("linking_method must be a non-empty string")

    def to_dict(self) -> dict[str, Any]:
        return {
            "claim_text": self.claim_text,
            "source_ref": self.source_ref,
            "relationship": self.relationship,
            "linking_method": self.linking_method,
        }


@dataclass(frozen=True)
class ClaimEvidenceLinkingResult:
    """Canonical result of linking extracted claims to available evidence sources."""

    status: str
    links: tuple[ClaimEvidenceLink, ...] = ()
    claim_count: int = 0
    linked_claim_count: int = 0
    source_count: int = 0
    linking_executed: bool = True
    reason: str | None = None

    def __post_init__(self) -> None:
        if self.status not in {"usable", "empty", "unavailable"}:
            raise ValueError("status must be usable, empty, or unavailable")
        if not isinstance(self.links, tuple) or any(not isinstance(link, ClaimEvidenceLink) for link in self.links):
            raise ValueError("links must be a tuple of ClaimEvidenceLink values")
        for value, name in ((self.claim_count, "claim_count"), (self.linked_claim_count, "linked_claim_count"), (self.source_count, "source_count")):
            if not isinstance(value, int) or value < 0:
                raise ValueError(f"{name} must be a non-negative integer")
        if self.linked_claim_count > self.claim_count:
            raise ValueError("linked_claim_count cannot exceed claim_count")
        if not isinstance(self.linking_executed, bool):
            raise ValueError("linking_executed must be a boolean")
        if self.status == "usable" and not self.links:
            raise ValueError("usable claim-evidence linking requires at least one link")
        if self.status == "empty" and self.links:
            raise ValueError("empty claim-evidence linking cannot contain links")
        if self.status == "unavailable" and self.links:
            raise ValueError("unavailable claim-evidence linking cannot contain links")
        if self.status == "unavailable" and (not isinstance(self.reason, str) or not self.reason.strip()):
            raise ValueError("unavailable claim-evidence linking requires a reason")
        if self.status != "unavailable" and self.reason is not None:
            raise ValueError("usable or empty claim-evidence linking cannot contain a reason")

    @classmethod
    def usable_result(cls, links: tuple[ClaimEvidenceLink, ...], claim_count: int, source_count: int) -> "ClaimEvidenceLinkingResult":
        linked_claim_count = len({link.claim_text for link in links})
        return cls("usable", links=links, claim_count=claim_count, linked_claim_count=linked_claim_count, source_count=source_count)

    @classmethod
    def empty_result(cls, claim_count: int, source_count: int) -> "ClaimEvidenceLinkingResult":
        return cls("empty", claim_count=claim_count, source_count=source_count)

    @classmethod
    def unavailable_result(cls, reason: str, claim_count: int = 0, source_count: int = 0) -> "ClaimEvidenceLinkingResult":
        return cls("unavailable", claim_count=claim_count, source_count=source_count, reason=reason)

    def to_dict(self) -> dict[str, Any]:
        return {
            "status": self.status,
            "links": [link.to_dict() for link in self.links],
            "link_count": len(self.links),
            "claim_count": self.claim_count,
            "linked_claim_count": self.linked_claim_count,
            "unlinked_claim_count": self.claim_count - self.linked_claim_count,
            "source_count": self.source_count,
            "linking_executed": self.linking_executed,
            "reason": self.reason,
        }


__all__ = ["ClaimEvidenceLink", "ClaimEvidenceLinkingResult"]