import pytest

from backend.app.models.base import BaseModelAdapter
from backend.app.models.provider_contract import (
    ModelProviderAdapter,
    MockModelProvider,
    get_provider_adapter,
)
from backend.app.models.registry import get_model_adapter


class DemoAdapter(BaseModelAdapter):
    def generate(self, task: str, context=None) -> dict:
        return {"text": task, "model": "demo-model", "provider": "demo"}


class DemoProvider(ModelProviderAdapter):
    @property
    def provider_name(self) -> str:
        return "demo"

    def create_adapter(self, model_name: str, profile: dict) -> BaseModelAdapter:
        return DemoAdapter()


def test_provider_contract_requires_provider_identity_and_factory():
    provider = DemoProvider()
    assert provider.provider_name == "demo"
    assert isinstance(provider.create_adapter("demo-model", {}), DemoAdapter)


def test_mock_provider_exposes_internal_identity():
    provider = MockModelProvider()
    assert provider.provider_name == "internal"


def test_provider_registry_resolves_internal_provider():
    provider = get_provider_adapter("internal")
    assert isinstance(provider, MockModelProvider)
    assert provider.provider_name == "internal"


def test_unknown_provider_returns_none():
    assert get_provider_adapter("unknown-provider") is None


def test_mock_provider_creates_mock_model_adapter():
    provider = MockModelProvider()
    adapter = provider.create_adapter("mock-model", {"provider": "internal"})
    assert adapter.__class__.__name__ == "MockModelAdapter"


def test_mock_provider_rejects_unknown_model():
    provider = MockModelProvider()
    with pytest.raises(ValueError, match="unsupported model"):
        provider.create_adapter("unknown-model", {"provider": "internal"})


def test_model_registry_resolves_model_through_provider_boundary():
    adapter = get_model_adapter("mock-model")
    assert adapter is not None
    result = adapter.generate("test task")
    assert result["model"] == "mock-model"
    assert result["provider"] == "internal"


def test_model_registry_returns_none_for_unknown_model():
    assert get_model_adapter("unknown-model") is None
