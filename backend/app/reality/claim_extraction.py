from dataclasses import dataclass
from typing import Any


@dataclass(frozen=True)
class EvidenceClaim:
    """A candidate factual claim extracted from grounded evidence."""

    text: str
    source_refs: tuple[str, ...] = ()
    extraction_method: str = "deterministic_sentence_split"

    def __post_init__(self) -> None:
        if not isinstance(self.text, str) or not self.text.strip():
            raise ValueError("claim text must be a non-empty string")
        if not isinstance(self.source_refs, tuple):
            raise ValueError("source_refs must be a tuple")
        if any(not isinstance(ref, str) or not ref.strip() for ref in self.source_refs):
            raise ValueError("source_refs must contain non-empty strings")
        if not isinstance(self.extraction_method, str) or not self.extraction_method.strip():
            raise ValueError("extraction_method must be a non-empty string")

    def to_dict(self) -> dict[str, Any]:
        return {
            "text": self.text,
            "source_refs": list(self.source_refs),
            "extraction_method": self.extraction_method,
        }


@dataclass(frozen=True)
class ClaimExtractionResult:
    """Canonical result of extracting candidate claims from evidence."""

    status: str
    claims: tuple[EvidenceClaim, ...] = ()
    source_count: int = 0
    extraction_executed: bool = True
    reason: str | None = None

    def __post_init__(self) -> None:
        if self.status not in {"usable", "empty", "unavailable"}:
            raise ValueError("status must be usable, empty, or unavailable")
        if not isinstance(self.claims, tuple) or any(not isinstance(claim, EvidenceClaim) for claim in self.claims):
            raise ValueError("claims must be a tuple of EvidenceClaim values")
        if not isinstance(self.source_count, int) or self.source_count < 0:
            raise ValueError("source_count must be a non-negative integer")
        if not isinstance(self.extraction_executed, bool):
            raise ValueError("extraction_executed must be a boolean")
        if self.status == "usable" and not self.extraction_executed:
            raise ValueError(
                "usable claim extraction requires extraction_executed to be True"
            )
        if self.status == "usable" and not self.claims:
            raise ValueError("usable claim extraction requires at least one claim")
        if self.status == "empty" and self.claims:
            raise ValueError("empty claim extraction cannot contain claims")
        if self.status == "unavailable" and self.claims:
            raise ValueError("unavailable claim extraction cannot contain claims")
        if self.status == "unavailable" and (not isinstance(self.reason, str) or not self.reason.strip()):
            raise ValueError("unavailable claim extraction requires a reason")
        if self.status != "unavailable" and self.reason is not None:
            raise ValueError("usable or empty claim extraction cannot contain a reason")

    @classmethod
    def validate(cls, result: object) -> "ClaimExtractionResult":
        """Validate an existing claim-extraction result."""
        if isinstance(result, cls):
            return result

        if not isinstance(result, dict):
            raise ValueError("claim extraction result must be a dictionary")

        required = {
            "status",
            "claims",
            "source_count",
            "extraction_executed",
        }
        if not required.issubset(result):
            raise ValueError("claim extraction result is missing required fields")

        raw_claims = result["claims"]
        if not isinstance(raw_claims, (list, tuple)):
            raise ValueError("claims must be a list or tuple")

        claims: list[EvidenceClaim] = []
        for raw_claim in raw_claims:
            if isinstance(raw_claim, EvidenceClaim):
                claims.append(raw_claim)
                continue
            if not isinstance(raw_claim, dict):
                raise ValueError("each claim must be a dictionary")
            required_claim_fields = {"text", "source_refs", "extraction_method"}
            if not required_claim_fields.issubset(raw_claim):
                raise ValueError("claim is missing required fields")
            source_refs = raw_claim["source_refs"]
            if not isinstance(source_refs, (list, tuple)):
                raise ValueError("claim source_refs must be a list or tuple")
            claims.append(
                EvidenceClaim(
                    text=raw_claim["text"],
                    source_refs=tuple(source_refs),
                    extraction_method=raw_claim["extraction_method"],
                )
            )

        return cls(
            status=result["status"],
            claims=tuple(claims),
            source_count=result["source_count"],
            extraction_executed=result["extraction_executed"],
            reason=result.get("reason"),
        )

    @classmethod
    def usable_result(cls, claims: tuple[EvidenceClaim, ...], source_count: int) -> "ClaimExtractionResult":
        return cls("usable", claims=claims, source_count=source_count)

    @classmethod
    def empty_result(cls, source_count: int = 0) -> "ClaimExtractionResult":
        return cls("empty", source_count=source_count)

    @classmethod
    def unavailable_result(cls, reason: str, source_count: int = 0) -> "ClaimExtractionResult":
        return cls("unavailable", source_count=source_count, reason=reason)

    def to_dict(self) -> dict[str, Any]:
        return {
            "status": self.status,
            "claims": [claim.to_dict() for claim in self.claims],
            "claim_count": len(self.claims),
            "source_count": self.source_count,
            "extraction_executed": self.extraction_executed,
            "reason": self.reason,
        }


__all__ = ["EvidenceClaim", "ClaimExtractionResult"]
