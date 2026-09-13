from dataclasses import dataclass
from typing import Any

from backend.app.reality.retrieval_provider_health_contract import RetrievalProviderHealth


@dataclass(frozen=True)
class RetrievalProviderHealthEvaluationResult:
    """Stable result produced by retrieval-provider health evaluation."""

    provider: str
    status: str
    supported: bool
    reason: str | None
    health_checked: bool
    evaluation_executed: bool = True

    def __post_init__(self) -> None:
        if not isinstance(self.provider, str) or not self.provider.strip():
            raise ValueError("provider must be a nonempty string")
        if self.status not in {"healthy", "unhealthy", "unknown"}:
            raise ValueError("status must be healthy, unhealthy, or unknown")
        if not isinstance(self.supported, bool):
            raise ValueError("supported must be a boolean")
        if self.reason is not None and (not isinstance(self.reason, str) or not self.reason.strip()):
            raise ValueError("reason must be a nonempty string when provided")
        if not isinstance(self.health_checked, bool):
            raise ValueError("health_checked must be a boolean")
        if not isinstance(self.evaluation_executed, bool):
            raise ValueError("evaluation_executed must be a boolean")
        expected_supported = self.status == "healthy"
        if self.supported != expected_supported:
            raise ValueError("supported must match the health status")

    @classmethod
    def healthy(cls, health: RetrievalProviderHealth) -> "RetrievalProviderHealthEvaluationResult":
        return cls(
            provider=health.provider,
            status="healthy",
            supported=True,
            reason=health.reason,
            health_checked=health.health_checked,
        )

    @classmethod
    def unhealthy(cls, health: RetrievalProviderHealth) -> "RetrievalProviderHealthEvaluationResult":
        return cls(
            provider=health.provider,
            status="unhealthy",
            supported=False,
            reason=health.reason or "retrieval_provider_unhealthy",
            health_checked=health.health_checked,
        )

    @classmethod
    def unknown(cls, health: RetrievalProviderHealth) -> "RetrievalProviderHealthEvaluationResult":
        return cls(
            provider=health.provider,
            status="unknown",
            supported=False,
            reason=health.reason or "retrieval_provider_health_unknown",
            health_checked=health.health_checked,
        )

    def to_dict(self) -> dict[str, Any]:
        return {
            "provider": self.provider,
            "status": self.status,
            "supported": self.supported,
            "reason": self.reason,
            "health_checked": self.health_checked,
            "evaluation_executed": self.evaluation_executed,
        }


__all__ = ["RetrievalProviderHealthEvaluationResult"]
