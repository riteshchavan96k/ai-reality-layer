from typing import Any

from backend.app.models.base import BaseModelAdapter


class MockModelAdapter(BaseModelAdapter):

    def generate(self, task: str, context: dict[str, Any] | None = None) -> dict:
        response = {
            "text": f"Mock response for: {task}",
            "model": "mock-model",
            "provider": "internal",
        }
        if context is not None:
            response["grounding"] = {
                "status": context.get("status"),
                "source_count": context.get("source_count", 0),
                "grounded": context.get("status") == "ready",
            }
        return response
