from collections.abc import Mapping
from dataclasses import dataclass
from typing import Any


MAX_REALITY_ENTITY_NAME_CHARS = 500


def normalize_explicit_entity_name(value: object) -> str:
    """Validate and normalize a caller-supplied real-world entity name."""
    if not isinstance(value, str):
        raise ValueError("entity name must be a string")
    normalized = value.strip()
    if not normalized:
        raise ValueError("entity name must be a non-empty string")
    if len(normalized) > MAX_REALITY_ENTITY_NAME_CHARS:
        raise ValueError(
            f"entity name must not exceed {MAX_REALITY_ENTITY_NAME_CHARS} characters"
        )
    return normalized


@dataclass(frozen=True)
class RealityEntity:
    """Canonical explicit entity identity attached to a Reality State."""

    status: str
    name: str | None
    identification_method: str

    def __post_init__(self) -> None:
        if self.status not in {"specified", "unspecified"}:
            raise ValueError("entity status must be specified or unspecified")

        if self.status == "specified":
            normalized = normalize_explicit_entity_name(self.name)
            if self.identification_method != "explicit_input":
                raise ValueError(
                    "specified entity requires explicit_input identification method"
                )
            object.__setattr__(self, "name", normalized)
            return

        if self.name is not None:
            raise ValueError("unspecified entity cannot contain a name")
        if self.identification_method != "not_provided":
            raise ValueError(
                "unspecified entity requires not_provided identification method"
            )

    @classmethod
    def specified(cls, name: str) -> "RealityEntity":
        return cls(
            status="specified",
            name=name,
            identification_method="explicit_input",
        )

    @classmethod
    def unspecified(cls) -> "RealityEntity":
        return cls(
            status="unspecified",
            name=None,
            identification_method="not_provided",
        )

    @classmethod
    def validate(cls, value: object) -> "RealityEntity":
        """Normalize explicit input, mappings, or an existing canonical entity."""
        if isinstance(value, cls):
            return value
        if value is None:
            return cls.unspecified()
        if isinstance(value, str):
            return cls.specified(value)
        if not isinstance(value, Mapping):
            raise ValueError(
                "entity must be a RealityEntity, mapping, string, or None"
            )

        required = {"status", "name", "identification_method"}
        missing = sorted(required - set(value))
        if missing:
            raise ValueError(
                f"entity is missing required fields: {', '.join(missing)}"
            )

        return cls(
            status=value["status"],
            name=value["name"],
            identification_method=value["identification_method"],
        )

    def to_dict(self) -> dict[str, Any]:
        return {
            "status": self.status,
            "name": self.name,
            "identification_method": self.identification_method,
        }


__all__ = [
    "MAX_REALITY_ENTITY_NAME_CHARS",
    "RealityEntity",
    "normalize_explicit_entity_name",
]
