import hashlib
from typing import Any

from backend.app.reality.source_provenance import SourceProvenance, SourceProvenanceResult
from backend.app.reality.source_provenance_normalizer import SourceProvenanceResultNormalizer


class SourceProvenanceBuilder:
    """Assign stable identities to the exact evidence source URIs."""

    def build_result(self, evidence: dict[str, Any]) -> SourceProvenanceResult:
        if not isinstance(evidence, dict):
            raise ValueError("evidence must be a dictionary")

        if evidence.get("status") != "usable":
            return SourceProvenanceResultNormalizer.normalize(
                SourceProvenanceResult.unavailable_result(
                    evidence.get("reason") or "evidence_not_usable"
                )
            )

        sources = evidence.get("sources", [])
        if not isinstance(sources, list):
            raise ValueError("evidence sources must be a list")
        if not sources:
            return SourceProvenanceResultNormalizer.normalize(SourceProvenanceResult.empty_result())

        records: list[SourceProvenance] = []
        seen_refs: set[str] = set()
        for source in sources:
            if not isinstance(source, dict):
                raise ValueError("each evidence source must be a dictionary")
            uri = source.get("uri")
            if not isinstance(uri, str) or not uri.strip():
                raise ValueError("each usable evidence source must include a non-empty uri")

            source_ref = uri
            if source_ref in seen_refs:
                continue
            seen_refs.add(source_ref)
            source_id = hashlib.sha256(uri.encode("utf-8")).hexdigest()
            records.append(
                SourceProvenance(
                    source_id=source_id,
                    source_ref=source_ref,
                    uri=uri,
                    title=source.get("title"),
                )
            )

        if not records:
            return SourceProvenanceResultNormalizer.normalize(SourceProvenanceResult.empty_result())
        return SourceProvenanceResultNormalizer.normalize(
            SourceProvenanceResult.usable_result(tuple(records))
        )

    def build(self, evidence: dict[str, Any]) -> dict[str, Any]:
        """Preserve a dictionary API while using the canonical result contract."""
        return self.build_result(evidence).to_dict()


__all__ = ["SourceProvenanceBuilder"]
