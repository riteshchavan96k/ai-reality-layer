import pytest

from backend.app.models.provider_config import ProviderConfig, get_provider_config
from backend.app.models.provider_contract import MockModelProvider, get_provider_adapter
from backend.app.models.registry import get_model_adapter


def test_provider_config_requires_provider_name():
    with pytest.raises(ValueError, match="provider_name"):
        ProviderConfig(provider_name=" ")


def test_provider_config_preserves_only_non_secret_configuration():
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


def test_internal_provider_has_no_external_configuration():
    config = get_provider_config("internal")
    assert config is not None
    assert config.provider_name == "internal"
    assert config.credential_env_var is None
    assert config.endpoint is None


def test_unknown_provider_config_returns_none():
    assert get_provider_config("unknown") is None


def test_provider_resolution_requires_configuration():
    provider = get_provider_adapter("internal")
    assert isinstance(provider, MockModelProvider)


def test_model_registry_still_resolves_mock_model():
    adapter = get_model_adapter("mock-model")
    assert adapter is not None
    result = adapter.generate("test task")
    assert result["model"] == "mock-model"
    assert result["provider"] == "internal"
