import pytest

from backend.app.models.provider_credential_resolver import ProviderCredentialResolver
from backend.app.models.provider_execution_gate import ProviderExecutionGate
from backend.app.models.provider_config import ProviderConfig, PROVIDER_CONFIGS


def test_internal_provider_does_not_require_credentials():
    result = ProviderCredentialResolver(environment={}).check("internal")
    assert result == {
        "status": "not_required",
        "provider": "internal",
        "credential_required": False,
        "credential_available": False,
        "credential_env_var": None,
    }


def test_unknown_provider_is_unconfigured():
    result = ProviderCredentialResolver(environment={}).check("unknown")
    assert result["status"] == "unconfigured"
    assert result["credential_required"] is False
    assert result["credential_available"] is False
    assert result["credential_env_var"] is None


def test_credential_reference_without_value_is_missing():
    PROVIDER_CONFIGS["test-provider"] = ProviderConfig(
        provider_name="test-provider",
        credential_env_var="ARL_TEST_SECRET",
    )
    try:
        result = ProviderCredentialResolver(environment={}).check("test-provider")
        assert result["status"] == "missing"
        assert result["credential_required"] is True
        assert result["credential_available"] is False
        assert result["credential_env_var"] == "ARL_TEST_SECRET"
    finally:
        PROVIDER_CONFIGS.pop("test-provider", None)


def test_nonempty_credential_value_is_reported_available_without_exposing_value():
    PROVIDER_CONFIGS["test-provider"] = ProviderConfig(
        provider_name="test-provider",
        credential_env_var="ARL_TEST_SECRET",
    )
    try:
        result = ProviderCredentialResolver(
            environment={"ARL_TEST_SECRET": "super-secret"}
        ).check("test-provider")
        assert result["status"] == "available"
        assert result["credential_available"] is True
        assert "super-secret" not in str(result)
    finally:
        PROVIDER_CONFIGS.pop("test-provider", None)


def test_provider_name_is_required():
    with pytest.raises(ValueError, match="provider_name"):
        ProviderCredentialResolver(environment={}).check(" ")


def test_execution_gate_allows_internal_provider():
    result = ProviderExecutionGate().check("internal")
    assert result["status"] == "allowed"
    assert result["credentials"]["status"] == "not_required"


def test_execution_gate_blocks_missing_credentials():
    PROVIDER_CONFIGS["test-provider"] = ProviderConfig(
        provider_name="test-provider",
        credential_env_var="ARL_TEST_SECRET",
    )
    try:
        resolver = ProviderCredentialResolver(environment={})
        gate = ProviderExecutionGate(credential_resolver=resolver)
        result = gate.check("test-provider")
        assert result["status"] == "blocked"
        assert result["credentials"]["status"] == "missing"
    finally:
        PROVIDER_CONFIGS.pop("test-provider", None)


def test_require_ready_reports_credential_block_reason():
    PROVIDER_CONFIGS["test-provider"] = ProviderConfig(
        provider_name="test-provider",
        credential_env_var="ARL_TEST_SECRET",
    )
    try:
        resolver = ProviderCredentialResolver(environment={})
        gate = ProviderExecutionGate(credential_resolver=resolver)
        with pytest.raises(RuntimeError, match="missing"):
            gate.require_ready("test-provider")
    finally:
        PROVIDER_CONFIGS.pop("test-provider", None)
