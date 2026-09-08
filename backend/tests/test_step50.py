import pytest

from backend.app.models.provider_invocation import (
    ProviderInvocationContract,
    ProviderInvocationRequest,
)


def test_invocation_request_requires_provider_name():
    with pytest.raises(ValueError, match="provider_name"):
        ProviderInvocationRequest(provider_name=" ", model_name="mock-model", task="hello")


def test_invocation_request_requires_model_name():
    with pytest.raises(ValueError, match="model_name"):
        ProviderInvocationRequest(provider_name="internal", model_name=" ", task="hello")


def test_invocation_request_requires_task():
    with pytest.raises(ValueError, match="task"):
        ProviderInvocationRequest(provider_name="internal", model_name="mock-model", task=" ")


def test_invocation_request_rejects_non_dict_context():
    with pytest.raises(ValueError, match="context"):
        ProviderInvocationRequest(
            provider_name="internal",
            model_name="mock-model",
            task="hello",
            context="invalid",
        )


def test_invocation_request_serializes_provider_neutral_envelope():
    request = ProviderInvocationRequest(
        provider_name="internal",
        model_name="mock-model",
        task="hello",
        context={"source_count": 1},
    )
    assert request.to_dict() == {
        "provider_name": "internal",
        "model_name": "mock-model",
        "task": "hello",
        "context": {"source_count": 1},
    }


def test_contract_builds_without_execution():
    result = ProviderInvocationContract().build(
        provider_name="internal",
        model_name="mock-model",
        task="hello",
    )
    assert result["status"] == "ready"
    assert result["execution_performed"] is False
    assert result["request"]["provider_name"] == "internal"
    assert result["request"]["model_name"] == "mock-model"


def test_contract_preserves_optional_context():
    result = ProviderInvocationContract().build(
        provider_name="internal",
        model_name="mock-model",
        task="hello",
        context={"grounded": True, "source_count": 2},
    )
    assert result["request"]["context"] == {
        "grounded": True,
        "source_count": 2,
    }


def test_contract_does_not_add_credentials_or_perform_network_execution():
    result = ProviderInvocationContract().build(
        provider_name="internal",
        model_name="mock-model",
        task="hello",
    )
    assert "credential" not in result
    assert "credentials" not in result
    assert result["execution_performed"] is False
