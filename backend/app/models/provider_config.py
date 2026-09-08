from dataclasses import dataclass
from typing import Any


@dataclass(frozen=True)
class ProviderConfig:
    """Non-secret configuration required to identify a model provider."""

    provider_name: str
    credential_env_var: str | None = None
    endpoint: str | None = None

    def __post_init__(self) -> None:
        if not isinstance(self.provider_name, str) or not self.provider_name.strip():
            raise ValueError("provider_name must be a non-empty string")
        if self.credential_env_var is not None and (
            not isinstance(self.credential_env_var, str) or not self.credential_env_var.strip()
        ):
            raise ValueError("credential_env_var must be a non-empty string when provided")
        if self.endpoint is not None and (
            not isinstance(self.endpoint, str) or not self.endpoint.strip()
        ):
            raise ValueError("endpoint must be a non-empty string when provided")

    def to_dict(self) -> dict[str, Any]:
        return {
            "provider_name": self.provider_name,
            "credential_env_var": self.credential_env_var,
            "endpoint": self.endpoint,
        }


PROVIDER_CONFIGS: dict[str, ProviderConfig] = {
    "internal": ProviderConfig(provider_name="internal"),
}


def get_provider_config(provider_name: str) -> ProviderConfig | None:
    return PROVIDER_CONFIGS.get(provider_name)
