from dataclasses import dataclass
from typing import Any

from backend.app.reality.retrieval_provider_availability import RetrievalProviderAvailability


@dataclass(frozen=True)
class RetrievalProviderAvailabilityEvaluationResult:
    """Stable result produced by retrieval-provider availability evaluation."""

    status: str
    supported: bool
    reason: str | None = None
    availability_checked: bool = True

    def __post_init__(self) -> None:
        if self.status not in {"available", "unavailable", "blocked"}:
            raise ValueError("status must be available, unavailable, or blocked")
        if not isinstance(self.supported, bool):
            raise ValueError("supported must be a boolean")
        if self.reason is not None and (not isinstance(self.reason, str) or not self.reason.strip()):
            raise ValueError("reason must be a nonempty string when provided")
        if not isinstance(self.availability_checked, bool):
            raise ValueError("availability_checked must be a boolean")
        if self.supported != (self.status == "available"):
            raise ValueError("supported must match the availability status")

    @classmethod
    def available_result(cls) -> "RetrievalProviderAvailabilityEvaluationResult":
        return cls(status="available", supported=True)

    @classmethod
    def unavailable_result(
        cls,
        reason: str = "retrieval_provider_unavailable",
    ) -> "RetrievalProviderAvailabilityEvaluationResult":
        return cls(status="unavailable", supported=False, reason=reason)

    @classmethod
    def blocked_result(
        cls,
        reason: str = "retrieval_provider_blocked",
    ) -> "RetrievalProviderAvailabilityEvaluationResult":
        return cls(status="blocked", supported=False, reason=reason)

    @classmethod
    def from_availability(
        cls,
        availability: RetrievalProviderAvailability,
    ) -> "RetrievalProviderAvailabilityEvaluationResult":
        if not isinstance(availability, RetrievalProviderAvailability):
            raise ValueError("availability must be a RetrievalProviderAvailability")
        if availability.status == "available":
            result = cls.available_result()
        elif availability.status == "blocked":
            result = cls.blocked_result(availability.reason or "retrieval_provider_blocked")
        else:
            result = cls.unavailable_result(availability.reason or "retrieval_provider_unavailable")
        return cls(
            status=result.status,
            supported=result.supported,
            reason=result.reason,
            availability_checked=availability.availability_checked,
        )

    @property
    def evaluation_executed(self) -> bool:
        return True

    def to_dict(self) -> dict[str, Any]:
        return {
            "status": self.status,
            "supported": self.supported,
            "reason": self.reason,
            "availability_checked": self.availability_checked,
            "evaluation_executed": self.evaluation_executed,
        }


__all__ = ["RetrievalProviderAvailabilityEvaluationResult"]
