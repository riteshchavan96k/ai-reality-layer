"""Strict-mode observation provenance for server-observed source captures.

Only reader-originated, exact-source-matched capture timestamps may override
caller-reported observation times. This concerns observation of text, NOT the
publisher's publication date or truth of a statement.
"""

from __future__ import annotations

from collections.abc import Mapping
from typing import Any

from backend.app.reality.source_observation import (
    SourceObservation, SourceObservationResult,
)
from backend.app.reality.source_provenance import SourceProvenanceResult
from backend.app.reality.submitted_evidence import SubmittedEvidenceBundle


def bind_server_capture_observations(
    bundle: SubmittedEvidenceBundle,
    provenance: SourceProvenanceResult,
    original: SourceObservationResult,
    assurance: Mapping[str, Any],
) -> SourceObservationResult:
    """Use independently captured time only for exact, verified source IDs.

    A pre-Step-221 backend reader may not supply capture metadata. Preserve
    its historical reported observation semantics if the caller supplied a
    timestamp, explicitly without claiming independent capture provenance.
    Without either capture or reported time the freshness signal is unavailable
    rather than silently using ingestion time as proof.
    """
    if not isinstance(bundle, SubmittedEvidenceBundle):
        raise ValueError("bundle must be SubmittedEvidenceBundle")
    if not isinstance(provenance, SourceProvenanceResult):
        raise ValueError("provenance must be SourceProvenanceResult")
    if not isinstance(original, SourceObservationResult):
        raise ValueError("original must be SourceObservationResult")
    if not isinstance(assurance, Mapping):
        raise ValueError("assurance must be a mapping")

    if provenance.status != "usable" or original.status != "usable":
        return original
    sources = assurance.get("sources")
    if not isinstance(sources, list) or len(sources) != len(bundle.documents):
        return SourceObservationResult.unavailable_result(
            "independent_capture_source_identity_mismatch"
        )
    by_uri: dict[str, Mapping[str, Any]] = {}
    for item in sources:
        if not isinstance(item, Mapping):
            return SourceObservationResult.unavailable_result(
                "independent_capture_source_identity_mismatch"
            )
        uri = item.get("source_ref")
        if not isinstance(uri, str) or uri in by_uri:
            return SourceObservationResult.unavailable_result(
                "independent_capture_source_identity_mismatch"
            )
        by_uri[uri] = item

    documents = {doc.uri: doc for doc in bundle.documents}
    original_by_id = {item.source_id: item for item in original.observations}
    if (
        set(documents) != set(by_uri)
        or {source.uri for source in provenance.sources} != set(documents)
        or len(original_by_id) != len(provenance.sources)
    ):
        return SourceObservationResult.unavailable_result(
            "independent_capture_source_identity_mismatch"
        )

    bound = []
    for source in provenance.sources:
        previous = original_by_id.get(source.source_id)
        if previous is None:
            return SourceObservationResult.unavailable_result(
                "independent_capture_source_identity_mismatch"
            )
        receipt = by_uri[source.uri]
        captured_at = receipt.get("capture_observed_at")
        if (
            receipt.get("status") == "exact_text_observed"
            and captured_at is not None
        ):
            # An invalid/future server timestamp must not crash an otherwise
            # safe request or fall back to an untrusted client timestamp.
            try:
                item = SourceObservation(
                    source_id=source.source_id,
                    observed_at=captured_at,
                    observation_method="independent_source_capture",
                )
            except (ValueError, TypeError):
                return SourceObservationResult.unavailable_result(
                    "invalid_independent_capture_observation_time"
                )
        else:
            if documents[source.uri].observed_at is None:
                return SourceObservationResult.unavailable_result(
                    "independent_capture_observation_required"
                )
            # Legacy/synthetic backend readers that do not produce captures:
            # preserve their old explicitly reported observation semantics.
            item = previous
        bound.append(item)
    return SourceObservationResult.usable_result(tuple(bound))


__all__ = ["bind_server_capture_observations"]
