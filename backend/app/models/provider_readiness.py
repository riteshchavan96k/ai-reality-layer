from typing import Any

from backend.app.models.provider_config import get_provider_config
from backend.app.models.provider_contract import get_provider_adapter


class ProviderReadinessChecker:
    """Check whether a configured provider can be used without exposing secrets."""

    def check(self, provider_name: str) -> dict[str, Any]:
        if not isinstance(provider_name, str) or not provider_name.strip():
            raise ValueError("provider_name must be a non-empty string")

        config = get_provider_config(provider_name)
        if config is None:
            return {
                "status": "unconfigured",
                "provider": provider_name,
                "adapter_available": False,
                "credential_configured": False,
                "endpoint_configured": False,
            }

        adapter = get_provider_adapter(provider_name)
        return {
            "status": "ready" if adapter is not None else "adapter_unavailable",
            "provider": provider_name,
            "adapter_available": adapter is not None,
            "credential_configured": config.credential_env_var is not None,
            "endpoint_configured": config.endpoint is not None,
        }
