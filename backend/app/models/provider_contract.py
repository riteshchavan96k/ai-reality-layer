from abc import ABC, abstractmethod
from typing import Any

from backend.app.models.base import BaseModelAdapter
from backend.app.models.provider_config import get_provider_config


class ModelProviderAdapter(ABC):
    """Provider boundary for constructing a model adapter from normalized metadata."""

    @property
    @abstractmethod
    def provider_name(self) -> str:
        pass

    @abstractmethod
    def create_adapter(
        self, model_name: str, profile: dict[str, Any]
    ) -> BaseModelAdapter:
        pass


class MockModelProvider(ModelProviderAdapter):
    """Internal provider implementation for the current mock model."""

    @property
    def provider_name(self) -> str:
        return "internal"

    def create_adapter(
        self, model_name: str, profile: dict[str, Any]
    ) -> BaseModelAdapter:
        from backend.app.models.mock_model import MockModelAdapter

        config = get_provider_config(self.provider_name)
        if config is None:
            raise ValueError("provider is not configured")
        if profile.get("provider") != config.provider_name:
            raise ValueError("model profile provider does not match provider")
        if model_name != "mock-model":
            raise ValueError("unsupported model for internal provider")
        return MockModelAdapter()


PROVIDER_REGISTRY: dict[str, type[ModelProviderAdapter]] = {
    "internal": MockModelProvider,
}


def get_provider_adapter(provider_name: str) -> ModelProviderAdapter | None:
    provider_class = PROVIDER_REGISTRY.get(provider_name)
    if provider_class is None:
        return None
    if get_provider_config(provider_name) is None:
        return None

    provider = provider_class()
    if provider.provider_name != provider_name:
        raise ValueError("provider registry identity does not match provider name")
    return provider
