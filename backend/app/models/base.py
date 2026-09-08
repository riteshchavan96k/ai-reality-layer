from abc import ABC, abstractmethod


class BaseModelAdapter(ABC):

    @abstractmethod
    def generate(self, task: str) -> dict:
        pass