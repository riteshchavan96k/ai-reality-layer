from dataclasses import dataclass


@dataclass
class ExecutionBudget:
    """Bound total model attempts across retries and fallback candidates."""

    max_attempts: int = 4
    used_attempts: int = 0

    def __post_init__(self) -> None:
        if self.max_attempts < 1:
            raise ValueError("max_attempts must be at least 1")
        if self.used_attempts < 0 or self.used_attempts > self.max_attempts:
            raise ValueError("used_attempts must be between 0 and max_attempts")

    @property
    def remaining_attempts(self) -> int:
        return self.max_attempts - self.used_attempts

    def consume(self, attempts: int) -> None:
        if attempts < 0:
            raise ValueError("attempts must not be negative")
        if attempts > self.remaining_attempts:
            raise ValueError("execution budget exceeded")
        self.used_attempts += attempts
