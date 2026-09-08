from typing import Any

from backend.app.models.provider_readiness import ProviderReadinessChecker


class ProviderExecutionGate:
    """Enforce provider readiness before a model adapter is used for execution."""

    def __init__(self, readiness_checker: ProviderReadinessChecker | None = None):
        self._readiness_checker = readiness_checker or ProviderReadinessChecker()

    def check(self, provider_name: str) -> dict[str, Any]:
        readiness = self._readiness_checker.check(provider_name)
        return {
            "status": "allowed" if readiness["status"] == "ready" else "blocked",
            "provider": readiness["provider"],
            "readiness": readiness,
        }

    def require_ready(self, provider_name: str) -> dict[str, Any]:
        result = self.check(provider_name)
        if result["status"] != "allowed":
            raise RuntimeError(
                f"provider execution blocked: {result['readiness']['status']}"
            )
        return result
