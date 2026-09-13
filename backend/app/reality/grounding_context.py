from typing import Any

from backend.app.reality.grounding_context_contract import GroundingContext


class EvidenceGroundingContextBuilder:
    """Build a stable, provenance-preserving context for downstream model execution."""

    def build_result(self, task: str, evidence: dict[str, Any]) -> GroundingContext:
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
            return GroundingContext.not_available_result(task)

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

        return GroundingContext.ready_result(
            task=task,
            content=content,
            sources=normalized_sources,
        )

    def build(self, task: str, evidence: dict[str, Any]) -> dict[str, Any]:
        """Preserve the legacy dictionary API while using the canonical contract."""
        return self.build_result(task, evidence).to_dict()
