from dataclasses import dataclass
from typing import Any


@dataclass(frozen=True)
class RetrievalProviderHealth:
    """Stable health state for a retrieval provider."""

    status: str
    reason: str | None = None
    health_checked: bool = True

    def __post_init__(self) -> None:
        if self.status not in {"healthy", "unhealthy", "unknown"}:
            raise ValueError("status must be healthy, unhealthy, or unknown")
        if self.reason is not None and (not isinstance(self.reason, str) or not self.reason.strip()):
            raise ValueError("reason must be a nonempty string when provided")
        if not isinstance(self.health_checked, bool):
            raise ValueError("health_checked must be a boolean")

    @classmethod
    def healthy(cls) -> "RetrievalProviderHealth":
        return cls("healthy")

    @classmethod
    def unhealthy(
        cls,
        reason: str = "retrieval_provider_unhealthy",
    ) -> "RetrievalProviderHealth":
        return cls("unhealthy", reason)

    @classmethod
    def unknown(
        cls,
        reason: str = "retrieval_provider_health_unknown",
    ) -> "RetrievalProviderHealth":
        return cls("unknown", reason)

    @property
    def is_healthy(self) -> bool:
        return self.status == "healthy"

    def to_dict(self) -> dict[str, Any]:
        return {
            "status": self.status,
            "reason": self.reason,
            "health_checked": self.health_checked,
        }


__all__ = ["RetrievalProviderHealth"]
