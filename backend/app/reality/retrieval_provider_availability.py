from dataclasses import dataclass
from typing import Any


@dataclass(frozen=True)
class RetrievalProviderAvailability:
    """Stable availability state for a retrieval provider."""

    status: str
    reason: str | None = None
    availability_checked: bool = True

    def __post_init__(self) -> None:
        if self.status not in {"available", "unavailable", "blocked"}:
            raise ValueError("status must be available, unavailable, or blocked")
        if self.reason is not None and (not isinstance(self.reason, str) or not self.reason.strip()):
            raise ValueError("reason must be a nonempty string when provided")
        if not isinstance(self.availability_checked, bool):
            raise ValueError("availability_checked must be a boolean")

    @classmethod
    def available(cls) -> "RetrievalProviderAvailability":
        return cls("available")

    @classmethod
    def unavailable(
        cls,
        reason: str = "retrieval_provider_unavailable",
    ) -> "RetrievalProviderAvailability":
        return cls("unavailable", reason)

    @classmethod
    def blocked(
        cls,
        reason: str = "retrieval_provider_blocked",
    ) -> "RetrievalProviderAvailability":
        return cls("blocked", reason)

    @property
    def is_available(self) -> bool:
        return self.status == "available"

    def to_dict(self) -> dict[str, Any]:
        return {
            "status": self.status,
            "reason": self.reason,
            "availability_checked": self.availability_checked,
        }


__all__ = ["RetrievalProviderAvailability"]
