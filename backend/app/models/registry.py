from backend.app.models.mock_model import MockModelAdapter


MODEL_REGISTRY = {
    "mock-model": MockModelAdapter,
}


def get_model_adapter(model_name: str):
    adapter_class = MODEL_REGISTRY.get(model_name)

    if adapter_class is None:
        return None

    return adapter_class()