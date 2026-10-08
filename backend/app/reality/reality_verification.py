from collections.abc import Mapping
from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Any


MAX_REALITY_VERIFIED_AT_CHARS = 64


def normalize_reality_verification_time(value: object) -> str:
    """Validate and canonicalize a Reality State verification timestamp."""
    if not isinstance(value, str):
        raise ValueError("verified_at must be a non-empty ISO-8601 string")
    if len(value) > MAX_REALITY_VERIFIED_AT_CHARS:
        raise ValueError(
            f"verified_at must not exceed {MAX_REALITY_VERIFIED_AT_CHARS} characters"
        )
    normalized = value.strip()
    if not normalized:
        raise ValueError("verified_at must be a non-empty ISO-8601 string")
    try:
        parsed = datetime.fromisoformat(normalized.replace("Z", "+00:00"))
    except ValueError as exc:
        raise ValueError("verified_at must be valid ISO-8601") from exc
    if parsed.tzinfo is None:
        raise ValueError("verified_at must include a timezone")
    verified_utc = parsed.astimezone(timezone.utc)
    if verified_utc > datetime.now(timezone.utc):
        raise ValueError("verified_at cannot be in the future")
    return verified_utc.isoformat().replace("+00:00", "Z")


@dataclass(frozen=True)
class RealityVerification:
    """Metadata describing completion of one deterministic Reality State verification pass."""

    status: str
    verified_at: str | None
    verification_method: str
    reason: str | None = None

    def __post_init__(self) -> None:
        if self.status not in {"completed", "not_completed"}:
            raise ValueError(
                "verification status must be completed or not_completed"
            )

        if self.status == "completed":
            if self.verified_at is None:
                raise ValueError(
                    "completed verification requires verified_at"
                )
            normalized = normalize_reality_verification_time(
                self.verified_at
            )
            object.__setattr__(self, "verified_at", normalized)
            if self.verification_method != "deterministic_pipeline_snapshot":
                raise ValueError(
                    "completed verification requires "
                    "deterministic_pipeline_snapshot method"
                )
            if self.reason is not None:
                raise ValueError(
                    "completed verification cannot contain a reason"
                )
            return

        if self.verified_at is not None:
            raise ValueError(
                "not_completed verification cannot contain verified_at"
            )
        if self.verification_method != "not_completed":
            raise ValueError(
                "not_completed verification requires not_completed method"
            )
        if (
            not isinstance(self.reason, str)
            or not self.reason.strip()
        ):
            raise ValueError(
                "not_completed verification requires a non-empty reason"
            )
        object.__setattr__(self, "reason", self.reason.strip())

    @classmethod
    def completed(cls, verified_at: str) -> "RealityVerification":
        return cls(
            status="completed",
            verified_at=verified_at,
            verification_method="deterministic_pipeline_snapshot",
        )

    @classmethod
    def not_completed(cls, reason: str) -> "RealityVerification":
        return cls(
            status="not_completed",
            verified_at=None,
            verification_method="not_completed",
            reason=reason,
        )

    @classmethod
    def validate(cls, value: object) -> "RealityVerification":
        """Normalize a canonical verification value or legacy absence."""
        if isinstance(value, cls):
            return value
        if value is None:
            return cls.not_completed("verification_metadata_unavailable")
        if not isinstance(value, Mapping):
            raise ValueError(
                "verification must be a RealityVerification, mapping, or None"
            )

        required = {
            "status",
            "verified_at",
            "verification_method",
            "reason",
        }
        missing = sorted(required - set(value))
        if missing:
            raise ValueError(
                "verification is missing required fields: "
                + ", ".join(missing)
            )

        return cls(
            status=value["status"],
            verified_at=value["verified_at"],
            verification_method=value["verification_method"],
            reason=value["reason"],
        )

    def to_dict(self) -> dict[str, Any]:
        return {
            "status": self.status,
            "verified_at": self.verified_at,
            "verification_method": self.verification_method,
            "reason": self.reason,
        }


__all__ = [
    "MAX_REALITY_VERIFIED_AT_CHARS",
    "RealityVerification",
    "normalize_reality_verification_time",
]
