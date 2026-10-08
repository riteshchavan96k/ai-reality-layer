from collections.abc import Mapping
from dataclasses import dataclass
from typing import Any


MAX_CLAIM_SEMANTIC_FIELD_CHARS = 10_000


def _normalize_semantic_field(value: object, field_name: str) -> str:
    if not isinstance(value, str):
        raise ValueError(f"{field_name} must be a non-empty string")
    normalized = value.strip()
    if not normalized:
        raise ValueError(f"{field_name} must be a non-empty string")
    if len(normalized) > MAX_CLAIM_SEMANTIC_FIELD_CHARS:
        raise ValueError(
            f"{field_name} must not exceed "
            f"{MAX_CLAIM_SEMANTIC_FIELD_CHARS} characters"
        )
    return normalized


@dataclass(frozen=True)
class ClaimSemanticStructure:
    """Canonical semantic representation attached to an evidence claim."""

    status: str
    subject: str | None
    predicate: str | None
    object: str | None
    structuring_method: str
    reason: str | None = None

    def __post_init__(self) -> None:
        if self.status not in {"structured", "unstructured"}:
            raise ValueError(
                "claim semantic status must be structured or unstructured"
            )

        if self.status == "structured":
            subject = _normalize_semantic_field(self.subject, "claim subject")
            predicate = _normalize_semantic_field(
                self.predicate,
                "claim predicate",
            )
            object_value = _normalize_semantic_field(
                self.object,
                "claim object",
            )
            if (
                not isinstance(self.structuring_method, str)
                or not self.structuring_method.strip()
                or self.structuring_method == "not_attempted"
            ):
                raise ValueError(
                    "structured claim requires a non-empty structuring method"
                )
            if self.reason is not None:
                raise ValueError(
                    "structured claim semantic structure cannot contain a reason"
                )
            object.__setattr__(self, "subject", subject)
            object.__setattr__(self, "predicate", predicate)
            object.__setattr__(self, "object", object_value)
            object.__setattr__(
                self,
                "structuring_method",
                self.structuring_method.strip(),
            )
            return

        if any(
            value is not None
            for value in (self.subject, self.predicate, self.object)
        ):
            raise ValueError(
                "unstructured claim cannot contain subject, predicate, or object"
            )
        if self.structuring_method != "not_attempted":
            raise ValueError(
                "unstructured claim requires not_attempted structuring method"
            )
        if (
            not isinstance(self.reason, str)
            or not self.reason.strip()
        ):
            raise ValueError(
                "unstructured claim requires a non-empty reason"
            )
        object.__setattr__(self, "reason", self.reason.strip())

    @classmethod
    def structured(
        cls,
        *,
        subject: str,
        predicate: str,
        object: str,
        structuring_method: str,
    ) -> "ClaimSemanticStructure":
        return cls(
            status="structured",
            subject=subject,
            predicate=predicate,
            object=object,
            structuring_method=structuring_method,
        )

    @classmethod
    def unstructured(
        cls,
        reason: str = "semantic_structuring_not_attempted",
    ) -> "ClaimSemanticStructure":
        return cls(
            status="unstructured",
            subject=None,
            predicate=None,
            object=None,
            structuring_method="not_attempted",
            reason=reason,
        )

    @classmethod
    def validate(cls, value: object) -> "ClaimSemanticStructure":
        """Normalize canonical, mapping-shaped, or legacy-absent structure."""
        if isinstance(value, cls):
            return value
        if value is None:
            return cls.unstructured()
        if not isinstance(value, Mapping):
            raise ValueError(
                "claim semantic structure must be a mapping, "
                "ClaimSemanticStructure, or None"
            )

        required = {
            "status",
            "subject",
            "predicate",
            "object",
            "structuring_method",
            "reason",
        }
        missing = sorted(required - set(value))
        if missing:
            raise ValueError(
                "claim semantic structure is missing required fields: "
                + ", ".join(missing)
            )

        return cls(
            status=value["status"],
            subject=value["subject"],
            predicate=value["predicate"],
            object=value["object"],
            structuring_method=value["structuring_method"],
            reason=value["reason"],
        )

    def to_dict(self) -> dict[str, Any]:
        return {
            "status": self.status,
            "subject": self.subject,
            "predicate": self.predicate,
            "object": self.object,
            "structuring_method": self.structuring_method,
            "reason": self.reason,
        }


__all__ = [
    "ClaimSemanticStructure",
    "MAX_CLAIM_SEMANTIC_FIELD_CHARS",
]
