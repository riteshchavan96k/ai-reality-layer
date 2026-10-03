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
            grounding_status = context.get(
                "grounding_status",
                context.get("status"),
            )
            response["grounding"] = {
                "status": grounding_status,
                "source_count": context.get("source_count", 0),
                "grounded": grounding_status == "ready",
            }
        return response
