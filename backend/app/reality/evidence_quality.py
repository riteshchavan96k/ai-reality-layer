from typing import Any
from urllib.parse import urlparse


class EvidenceQualityValidator:
    """Validate structural quality and provenance of normalized retrieval evidence."""

    def validate(self, evidence: dict[str, Any]) -> dict[str, Any]:
        if not isinstance(evidence, dict):
            raise ValueError("evidence must be a dictionary")

        status = evidence.get("status")
        sources = evidence.get("sources", [])
        content = evidence.get("content")

        if not isinstance(sources, list):
            raise ValueError("evidence sources must be a list")
        if content is not None and not isinstance(content, str):
            raise ValueError("evidence content must be a string or None")

        issues: list[str] = []
        provenance_complete = True

        for source in sources:
            if not isinstance(source, dict):
                raise ValueError("each evidence source must be a dictionary")

            title = source.get("title")
            uri = source.get("uri")
            if title is None and uri is None:
                provenance_complete = False
                issues.append("source_missing_provenance")
                continue

            if uri is not None:
                parsed = urlparse(str(uri))
                if parsed.scheme not in {"http", "https"} or not parsed.netloc:
                    provenance_complete = False
                    issues.append("source_invalid_uri")

        has_content = bool(content and content.strip())
        source_count = len(sources)

        if status == "not_required":
            return {
                "status": "not_required",
                "usable": False,
                "source_count": source_count,
                "has_content": has_content,
                "provenance_complete": provenance_complete,
                "issues": issues,
            }

        if status != "completed":
            issues.append("retrieval_not_completed")
            return {
                "status": "insufficient",
                "usable": False,
                "source_count": source_count,
                "has_content": has_content,
                "provenance_complete": provenance_complete,
                "issues": issues,
            }

        if source_count == 0:
            issues.append("no_sources")
        if not has_content:
            issues.append("no_content")
        if not provenance_complete:
            issues.append("incomplete_provenance")

        usable = bool(source_count and has_content and provenance_complete and not issues)
        return {
            "status": "usable" if usable else "insufficient",
            "usable": usable,
            "source_count": source_count,
            "has_content": has_content,
            "provenance_complete": provenance_complete,
            "issues": issues,
        }
