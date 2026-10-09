from typing import Any
from urllib.parse import urlparse

from backend.app.reality.evidence_normalization import EvidenceNormalizationResult
from backend.app.reality.source_observation import normalize_reported_observation_time
from backend.app.reality.retrieval_input_bounds import validate_retrieved_evidence_bounds


class RetrievalEvidenceNormalizer:
    """Normalize retrieval output into a stable, provenance-preserving evidence shape."""

    def normalize_result(self, retrieval: dict[str, Any]) -> EvidenceNormalizationResult:
        """Preserve per-source text; reject contradictory or unattributed evidence."""
        if not isinstance(retrieval, dict):
            raise ValueError("retrieval result must be a dictionary")

        status = retrieval.get("status")
        sources = retrieval.get("sources", [])
        content = retrieval.get("content")

        if not isinstance(sources, list):
            raise ValueError("retrieval sources must be a list")
        if any(not isinstance(source, dict) for source in sources):
            raise ValueError("each retrieval source must be a dictionary")
        if content is not None and not isinstance(content, str):
            raise ValueError("retrieval content must be a string or None")

        if status == "completed":
            bounds_reason = validate_retrieved_evidence_bounds(sources, content)
            if bounds_reason is not None:
                return EvidenceNormalizationResult(
                    status="invalid_evidence",
                    sources=[],
                    content=None,
                    source_count=0,
                    has_content=False,
                )

        normalized_sources: list[dict[str, Any]] = []
        invalid_observation = False
        for source in sources:
            if not isinstance(source, dict):
                raise ValueError("each retrieval source must be a dictionary")

            title = source.get("title")
            uri = source.get("uri")
            if title is None and uri is None:
                raise ValueError("each retrieval source must include title or uri")

            normalized_source: dict[str, Any] = {
                "title": str(title) if title is not None else None,
                "uri": (
                    uri.strip() if isinstance(uri, str)
                    else str(uri) if uri is not None else None
                ),
            }
            # Never discard the per-source payload before claim extraction.
            if "content" in source:
                normalized_source["content"] = source["content"]
            if "observed_at" in source:
                try:
                    normalized_source["observed_at"] = (
                        normalize_reported_observation_time(source["observed_at"])
                    )
                except ValueError:
                    invalid_observation = True
            normalized_sources.append(normalized_source)

        normalized_status = status or "unknown"
        if status == "completed":
            scoped = ["content" in source for source in normalized_sources]
            invalid_attribution = invalid_observation or bool(
                normalized_sources and any(
                    not source.get("uri") for source in normalized_sources
                )
            )
            uris = [source["uri"] for source in normalized_sources]
            if len(uris) != len(set(uris)):
                invalid_attribution = True

            if any(scoped):
                if not all(scoped) or any(
                    not isinstance(source["content"], str)
                    or not source["content"].strip()
                    for source in normalized_sources
                    if "content" in source
                ):
                    invalid_attribution = True
                else:
                    joined = "\n\n".join(
                        source["content"].strip()
                        for source in normalized_sources
                    )
                    if content is not None and content.strip() != joined:
                        invalid_attribution = True
                    else:
                        content = joined

            if invalid_attribution or (not normalized_sources and not content):
                normalized_status = "invalid_evidence"

        if normalized_status == "invalid_evidence":
            content = None

        return EvidenceNormalizationResult(
            status=normalized_status,
            sources=normalized_sources,
            content=content,
            source_count=len(normalized_sources),
            has_content=bool(content and content.strip()),
        )

    def normalize(self, retrieval: dict[str, Any]) -> dict[str, Any]:
        """Preserve the legacy dictionary API while using the canonical result contract."""
        return self.normalize_result(retrieval).to_dict()
