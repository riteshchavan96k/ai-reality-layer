import pytest

from backend.app.models.provider_execution_gate import ProviderExecutionGate


def test_internal_provider_execution_is_allowed():
    result = ProviderExecutionGate().check("internal")

    assert result["status"] == "allowed"
    assert result["provider"] == "internal"
    assert result["readiness"]["status"] == "ready"


def test_unknown_provider_execution_is_blocked():
    result = ProviderExecutionGate().check("unknown")

    assert result["status"] == "blocked"
    assert result["readiness"]["status"] == "unconfigured"


def test_require_ready_returns_readiness_for_ready_provider():
    result = ProviderExecutionGate().require_ready("internal")

    assert result["status"] == "allowed"
    assert result["readiness"]["adapter_available"] is True


def test_require_ready_blocks_unconfigured_provider():
    with pytest.raises(RuntimeError, match="provider execution blocked: unconfigured"):
        ProviderExecutionGate().require_ready("unknown")
