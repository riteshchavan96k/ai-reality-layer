from typing import Any


class GroundedResultEnvelopeBuilder:
    """Build a provider-independent grounding envelope for an executed result."""

    def build(self, grounding_context: dict[str, Any], result: Any) -> dict[str, Any]:
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

        normalized_sources: list[dict[str, Any]] = []
        for source in sources:
            if not isinstance(source, dict):
                raise ValueError("each grounding source must be a dictionary")
            normalized_sources.append(
                {
                    "title": source.get("title"),
                    "uri": source.get("uri"),
                }
            )

        return {
            "status": status,
            "grounded": status == "ready",
            "source_count": len(normalized_sources),
            "sources": normalized_sources,
        }
