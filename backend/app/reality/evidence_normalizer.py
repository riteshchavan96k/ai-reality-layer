from typing import Any


class RetrievalEvidenceNormalizer:
    """Normalize retrieval output into a stable, provenance-preserving evidence shape."""

    def normalize(self, retrieval: dict[str, Any]) -> dict[str, Any]:
        if not isinstance(retrieval, dict):
            raise ValueError("retrieval result must be a dictionary")

        status = retrieval.get("status")
        sources = retrieval.get("sources", [])
        content = retrieval.get("content")

        if not isinstance(sources, list):
            raise ValueError("retrieval sources must be a list")

        normalized_sources: list[dict[str, Any]] = []
        for source in sources:
            if not isinstance(source, dict):
                raise ValueError("each retrieval source must be a dictionary")

            title = source.get("title")
            uri = source.get("uri")
            if title is None and uri is None:
                raise ValueError("each retrieval source must include title or uri")

            normalized_sources.append(
                {
                    "title": str(title) if title is not None else None,
                    "uri": str(uri) if uri is not None else None,
                }
            )

        if content is not None and not isinstance(content, str):
            raise ValueError("retrieval content must be a string or None")

        if status == "completed" and not normalized_sources and not content:
            return {
                "status": "invalid_evidence",
                "sources": [],
                "content": None,
                "source_count": 0,
                "has_content": False,
            }

        return {
            "status": status or "unknown",
            "sources": normalized_sources,
            "content": content,
            "source_count": len(normalized_sources),
            "has_content": bool(content and content.strip()),
        }
