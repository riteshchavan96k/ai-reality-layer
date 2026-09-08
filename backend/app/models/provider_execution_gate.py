from typing import Any

from backend.app.models.provider_credential_resolver import ProviderCredentialResolver
from backend.app.models.provider_readiness import ProviderReadinessChecker


class ProviderExecutionGate:
    """Enforce provider readiness and credential availability before execution."""

    def __init__(
        self,
        readiness_checker: ProviderReadinessChecker | None = None,
        credential_resolver: ProviderCredentialResolver | None = None,
    ):
        self._readiness_checker = readiness_checker or ProviderReadinessChecker()
        self._credential_resolver = credential_resolver or ProviderCredentialResolver()

    def check(self, provider_name: str) -> dict[str, Any]:
        readiness = self._readiness_checker.check(provider_name)
        if readiness["status"] != "ready":
            return {
                "status": "blocked",
                "provider": readiness["provider"],
                "readiness": readiness,
                "credentials": None,
            }

        credentials = self._credential_resolver.check(provider_name)
        credentials_required = credentials["credential_required"]
        credentials_available = credentials["credential_available"]
        allowed = not credentials_required or credentials_available

        return {
            "status": "allowed" if allowed else "blocked",
            "provider": provider_name,
            "readiness": readiness,
            "credentials": credentials,
        }

    def require_ready(self, provider_name: str) -> dict[str, Any]:
        result = self.check(provider_name)
        if result["status"] != "allowed":
            if result["credentials"] is not None:
                reason = result["credentials"]["status"]
            else:
                reason = result["readiness"]["status"]
            raise RuntimeError(f"provider execution blocked: {reason}")
        return result
