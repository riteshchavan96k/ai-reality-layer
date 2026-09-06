from abc import ABC, abstractmethod
from typing import Any


class BaseModelAdapter(ABC):

    @abstractmethod
    def generate(self, task: str, context: dict[str, Any] | None = None) -> dict:
        pass
