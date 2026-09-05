from dataclasses import dataclass
from typing import Callable, Any


@dataclass(frozen=True)
class RetryPolicy:
    """Deterministic retry policy for transient model execution failures."""

    max_attempts: int = 2

    def __post_init__(self) -> None:
        if self.max_attempts < 1:
            raise ValueError("max_attempts must be at least 1")

    def execute(self, operation: Callable[[], Any]) -> dict:
        attempts = 0
        last_error = None

        while attempts < self.max_attempts:
            attempts += 1
            try:
                result = operation()
                return {
                    "status": "success",
                    "attempts": attempts,
                    "result": result,
                }
            except Exception as exc:
                last_error = str(exc)

        return {
            "status": "failed",
            "attempts": attempts,
            "error": last_error,
        }
