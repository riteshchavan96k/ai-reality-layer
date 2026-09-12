from dataclasses import dataclass
from typing import Any


@dataclass(frozen=True)
class RetrievalProviderIdentity:
    """Stable identity for a retrieval provider."""

    name: str

    def __post_init__(self) -> None:
        if not isinstance(self.name, str) or not self.name.strip():
            raise ValueError("provider identity name must be a nonempty string")

    def to_dict(self) -> dict[str, Any]:
        return {"name": self.name}


__all__ = ["RetrievalProviderIdentity"]
