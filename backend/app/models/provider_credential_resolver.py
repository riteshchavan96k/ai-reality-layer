import os
from collections.abc import Mapping
from typing import Any

from backend.app.models.provider_config import get_provider_config


class ProviderCredentialResolver:
    """Check credential availability without exposing credential values."""

    def __init__(self, environment: Mapping[str, str] | None = None):
        self._environment = environment if environment is not None else os.environ

    def check(self, provider_name: str) -> dict[str, Any]:
        if not isinstance(provider_name, str) or not provider_name.strip():
            raise ValueError("provider_name must be a non-empty string")

        config = get_provider_config(provider_name)
        if config is None:
            return {
                "status": "unconfigured",
                "provider": provider_name,
                "credential_required": False,
                "credential_available": False,
                "credential_env_var": None,
            }

        if config.credential_env_var is None:
            return {
                "status": "not_required",
                "provider": provider_name,
                "credential_required": False,
                "credential_available": False,
                "credential_env_var": None,
            }

        credential_available = bool(
            self._environment.get(config.credential_env_var, "").strip()
        )

        return {
            "status": "available" if credential_available else "missing",
            "provider": provider_name,
            "credential_required": True,
            "credential_available": credential_available,
            "credential_env_var": config.credential_env_var,
        }
