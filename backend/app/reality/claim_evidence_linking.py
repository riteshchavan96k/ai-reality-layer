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
    def validate(cls, raw_result: object) -> "ClaimEvidenceLinkingResult":
        """Validate or normalize a canonical claim-evidence linking result."""
        if isinstance(raw_result, cls):
            return raw_result
        if not isinstance(raw_result, dict):
            raise ValueError("claim-evidence linking result must be a mapping or ClaimEvidenceLinkingResult")

        required = {
            "status",
            "links",
            "claim_count",
            "linked_claim_count",
            "source_count",
            "linking_executed",
            "reason",
        }
        missing = sorted(required - set(raw_result))
        if missing:
            raise ValueError(f"missing required fields: {', '.join(missing)}")

        raw_links = raw_result["links"]
        if not isinstance(raw_links, (list, tuple)):
            raise ValueError("links must be a list or tuple")

        links: list[ClaimEvidenceLink] = []
        for raw_link in raw_links:
            if isinstance(raw_link, ClaimEvidenceLink):
                links.append(raw_link)
                continue
            if not isinstance(raw_link, dict):
                raise ValueError("each claim-evidence link must be a mapping or ClaimEvidenceLink")
            link_required = {"claim_text", "source_ref", "relationship", "linking_method"}
            link_missing = sorted(link_required - set(raw_link))
            if link_missing:
                raise ValueError(f"claim-evidence link is missing required fields: {', '.join(link_missing)}")
            links.append(
                ClaimEvidenceLink(
                    claim_text=raw_link["claim_text"],
                    source_ref=raw_link["source_ref"],
                    relationship=raw_link["relationship"],
                    linking_method=raw_link["linking_method"],
                )
            )

        return cls(
            status=raw_result["status"],
            links=tuple(links),
            claim_count=raw_result["claim_count"],
            linked_claim_count=raw_result["linked_claim_count"],
            source_count=raw_result["source_count"],
            linking_executed=raw_result["linking_executed"],
            reason=raw_result["reason"],
        )

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
