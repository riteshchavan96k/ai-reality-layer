from dataclasses import dataclass
from typing import Any


@dataclass(frozen=True)
class GroundedSource:
    """Canonical source reference exposed by the grounded-result envelope."""

    title: str | None
    uri: str | None

    def __post_init__(self) -> None:
        if self.title is not None and not isinstance(self.title, str):
            raise ValueError("grounding source title must be a string or None")
        if self.uri is not None and not isinstance(self.uri, str):
            raise ValueError("grounding source uri must be a string or None")

    def to_dict(self) -> dict[str, Any]:
        return {"title": self.title, "uri": self.uri}


@dataclass(frozen=True)
class GroundedResultEnvelope:
    """Canonical provider-independent grounding envelope."""

    status: str
    grounded: bool
    source_count: int
    sources: tuple[GroundedSource, ...]

    def __post_init__(self) -> None:
        if self.status not in {"ready", "not_available"}:
            raise ValueError("status must be ready or not_available")
        if not isinstance(self.grounded, bool):
            raise ValueError("grounded must be a boolean")
        if self.grounded != (self.status == "ready"):
            raise ValueError("grounded must match status")
        if not isinstance(self.source_count, int) or self.source_count < 0:
            raise ValueError("source_count must be a non-negative integer")
        if not isinstance(self.sources, tuple) or any(not isinstance(item, GroundedSource) for item in self.sources):
            raise ValueError("sources must be a tuple of GroundedSource values")
        if self.source_count != len(self.sources):
            raise ValueError("source_count must match sources")
        if self.status == "not_available" and self.sources:
            raise ValueError("not_available envelope cannot contain sources")

    @classmethod
    def validate(cls, raw_result: object) -> "GroundedResultEnvelope":
        """Validate or normalize a canonical grounded-result envelope."""
        if isinstance(raw_result, cls):
            return raw_result
        if not isinstance(raw_result, dict):
            raise ValueError("grounded result must be a mapping or GroundedResultEnvelope")
        required = {"status", "grounded", "source_count", "sources"}
        missing = sorted(required - set(raw_result))
        if missing:
            raise ValueError(f"missing required fields: {', '.join(missing)}")
        raw_sources = raw_result["sources"]
        if not isinstance(raw_sources, (list, tuple)):
            raise ValueError("sources must be a list or tuple")
        sources: list[GroundedSource] = []
        for raw_source in raw_sources:
            if isinstance(raw_source, GroundedSource):
                sources.append(raw_source)
                continue
            if not isinstance(raw_source, dict):
                raise ValueError("each grounding source must be a mapping or GroundedSource")
            sources.append(GroundedSource(raw_source.get("title"), raw_source.get("uri")))
        return cls(
            status=raw_result["status"],
            grounded=raw_result["grounded"],
            source_count=raw_result["source_count"],
            sources=tuple(sources),
        )

    def to_dict(self) -> dict[str, Any]:
        return {
            "status": self.status,
            "grounded": self.grounded,
            "source_count": self.source_count,
            "sources": [source.to_dict() for source in self.sources],
        }


class GroundedResultEnvelopeBuilder:
    """Build a provider-independent grounding envelope for an executed result."""

    def build_result(self, grounding_context: dict[str, Any], result: Any) -> GroundedResultEnvelope:
        if not isinstance(grounding_context, dict):
            raise ValueError("grounding_context must be a dictionary")

        status = grounding_context.get("status")
        source_count = grounding_context.get("source_count", 0)
        sources = grounding_context.get("sources", [])

        if status not in {"ready", "not_available"}:
            raise ValueError("grounding_context has an invalid status")
        if not isinstance(source_count, int) or source_count < 0:
            raise ValueError("grounding_context source_count must be a non-negative integer")
        if not isinstance(sources, list):
            raise ValueError("grounding_context sources must be a list")

        if status == "ready":
            if source_count != len(sources):
                raise ValueError("grounding_context source_count does not match sources")
            if result is None:
                raise ValueError("result must be present for a ready grounding context")
        elif sources:
            raise ValueError("not_available grounding context cannot contain sources")

        normalized_sources = tuple(
            GroundedSource(source.get("title"), source.get("uri"))
            if isinstance(source, dict)
            else (_ for _ in ()).throw(ValueError("each grounding source must be a dictionary"))
            for source in sources
        )
        from backend.app.reality.grounded_result_normalizer import GroundedResultEnvelopeNormalizer

        return GroundedResultEnvelopeNormalizer.normalize(
            GroundedResultEnvelope(
                status=status,
                grounded=status == "ready",
                source_count=len(normalized_sources),
                sources=normalized_sources,
            )
        )

    def build(self, grounding_context: dict[str, Any], result: Any) -> dict[str, Any]:
        return self.build_result(grounding_context, result).to_dict()


__all__ = ["GroundedSource", "GroundedResultEnvelope", "GroundedResultEnvelopeBuilder"]
