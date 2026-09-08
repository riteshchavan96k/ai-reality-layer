from typing import Any


class ModelCapabilityContract:
    """Validate and normalize provider-independent model capability metadata."""

    def normalize(self, model_name: str, profile: dict[str, Any]) -> dict[str, Any]:
        if not isinstance(model_name, str) or not model_name.strip():
            raise ValueError("model_name must be a non-empty string")
        if not isinstance(profile, dict):
            raise ValueError("model profile must be a dictionary")

        name = profile.get("name") or model_name
        provider = profile.get("provider")
        capabilities = profile.get("capabilities", [])

        if not isinstance(name, str) or not name.strip():
            raise ValueError("model profile name must be a non-empty string")
        if not isinstance(provider, str) or not provider.strip():
            raise ValueError("model profile provider must be a non-empty string")
        if not isinstance(capabilities, list):
            raise ValueError("model profile capabilities must be a list")
        if not capabilities or any(
            not isinstance(capability, str) or not capability.strip()
            for capability in capabilities
        ):
            raise ValueError("model profile capabilities must contain non-empty strings")

        normalized: dict[str, Any] = {
            "name": name,
            "provider": provider,
            "capabilities": list(dict.fromkeys(capabilities)),
        }

        for key in ("context_window", "supports_grounding"):
            if key in profile:
                normalized[key] = profile[key]

        return normalized

    def normalize_catalog(
        self, catalog: dict[str, dict[str, Any]]
    ) -> dict[str, dict[str, Any]]:
        if not isinstance(catalog, dict):
            raise ValueError("model catalog must be a dictionary")

        return {
            model_name: self.normalize(model_name, profile)
            for model_name, profile in catalog.items()
        }
