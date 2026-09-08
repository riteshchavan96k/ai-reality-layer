import pytest

from backend.app.models.provider_readiness import ProviderReadinessChecker


def test_internal_provider_is_ready():
    result = ProviderReadinessChecker().check("internal")
    assert result == {
        "status": "ready",
        "provider": "internal",
        "adapter_available": True,
        "credential_configured": False,
        "endpoint_configured": False,
    }


def test_unknown_provider_is_unconfigured():
    result = ProviderReadinessChecker().check("unknown")
    assert result["status"] == "unconfigured"
    assert result["adapter_available"] is False
    assert result["credential_configured"] is False
    assert result["endpoint_configured"] is False


def test_provider_name_is_required():
    with pytest.raises(ValueError, match="provider_name"):
        ProviderReadinessChecker().check(" ")
