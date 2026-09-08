MODEL_CATALOG = {
    "mock-model": {
        "name": "Mock Model",
        "provider": "internal",
        "capabilities": [
            "programming",
            "reasoning",
            "long_context",
            "general",
        ],
    }
}


def get_available_models() -> list[str]:
    return list(MODEL_CATALOG.keys())
