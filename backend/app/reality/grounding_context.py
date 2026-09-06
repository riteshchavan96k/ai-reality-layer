from typing import Any


class EvidenceGroundingContextBuilder:
    """Build a stable, provenance-preserving context for downstream model execution."""

    def build(self, task: str, evidence: dict[str, Any]) -> dict[str, Any]:
        if not isinstance(task, str) or not task.strip():
            raise ValueError("task must be a non-empty string")
        if not isinstance(evidence, dict):
            raise ValueError("evidence must be a dictionary")

        status = evidence.get("status")
        sources = evidence.get("sources", [])
        content = evidence.get("content")

        if not isinstance(sources, list):
            raise ValueError("evidence sources must be a list")
        if content is not None and not isinstance(content, str):
            raise ValueError("evidence content must be a string or None")

        if status != "usable":
            return {
                "status": "not_available",
                "task": task,
                "content": None,
                "sources": [],
                "source_count": 0,
            }

        normalized_sources: list[dict[str, Any]] = []
        for source in sources:
            if not isinstance(source, dict):
                raise ValueError("each evidence source must be a dictionary")
            normalized_sources.append(
                {
                    "title": source.get("title"),
                    "uri": source.get("uri"),
                }
            )

        return {
            "status": "ready",
            "task": task,
            "content": content,
            "sources": normalized_sources,
            "source_count": len(normalized_sources),
        }
