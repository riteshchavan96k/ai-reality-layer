from typing import Any
from urllib.parse import urlparse

from backend.app.reality.evidence_normalization import EvidenceNormalizationResult


class RetrievalEvidenceNormalizer:
    """Normalize retrieval output into a stable, provenance-preserving evidence shape."""

    def normalize_result(self, retrieval: dict[str, Any]) -> EvidenceNormalizationResult:
        """Return the canonical evidence normalization result contract."""
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

        normalized_status = status or "unknown"
        if status == "completed" and not normalized_sources and not content:
            normalized_status = "invalid_evidence"

        return EvidenceNormalizationResult(
            status=normalized_status,
            sources=normalized_sources,
            content=content if normalized_status != "invalid_evidence" else None,
            source_count=len(normalized_sources),
            has_content=bool(content and content.strip()) if normalized_status != "invalid_evidence" else False,
        )

    def normalize(self, retrieval: dict[str, Any]) -> dict[str, Any]:
        """Preserve the legacy dictionary API while using the canonical result contract."""
        return self.normalize_result(retrieval).to_dict()
