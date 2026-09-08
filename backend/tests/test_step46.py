import pytest

from backend.app.models.provider_config import ProviderConfig, get_provider_config


def test_provider_config_requires_provider_name():
    with pytest.raises(ValueError, match="provider_name"):
        ProviderConfig(provider_name=" ")


def test_provider_config_accepts_non_secret_metadata():
    config = ProviderConfig(
        provider_name="example",
        credential_env_var="EXAMPLE_API_KEY",
        endpoint="https://api.example.com",
    )
    assert config.to_dict() == {
        "provider_name": "example",
        "credential_env_var": "EXAMPLE_API_KEY",
        "endpoint": "https://api.example.com",
    }


def test_provider_config_rejects_empty_credential_reference():
    with pytest.raises(ValueError, match="credential_env_var"):
        ProviderConfig(provider_name="example", credential_env_var=" ")


def test_provider_config_rejects_empty_endpoint():
    with pytest.raises(ValueError, match="endpoint"):
        ProviderConfig(provider_name="example", endpoint=" ")


def test_internal_provider_has_no_external_credential_requirement():
    config = get_provider_config("internal")
    assert config is not None
    assert config.provider_name == "internal"
    assert config.credential_env_var is None
    assert config.endpoint is None


def test_unknown_provider_config_returns_none():
    assert get_provider_config("unknown") is None
