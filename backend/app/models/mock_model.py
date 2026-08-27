from backend.app.models.base import BaseModelAdapter


class MockModelAdapter(BaseModelAdapter):

    def generate(self, task: str) -> dict:
        return {
            "text": f"Mock response for: {task}",
            "model": "mock-model",
            "provider": "internal",
        }