"""Resource limits for untrusted retrieval evidence.

Submitted evidence already has equivalent per-document limits. Apply these
at the configured-HTTP and provider-neutral boundaries before claim splitting.
"""
from typing import Any

from backend.app.reality.source_observation import MAX_SOURCE_OBSERVED_AT_CHARS


# Match the direct-evidence MVP limits. Keep this module dependency-free:
# submitted_evidence imports the claim extractor, which uses these limits.
MAX_RETRIEVED_SOURCES = 20
MAX_RETRIEVED_SOURCE_CONTENT_CHARS = 50_000
MAX_RETRIEVED_TITLE_CHARS = 500
MAX_RETRIEVED_URI_CHARS = 2_048
MAX_RETRIEVED_OBSERVED_AT_CHARS = MAX_SOURCE_OBSERVED_AT_CHARS
MAX_RETRIEVED_CLAIMS = 2_000

# Canonical pipeline-consumed fields. Early provider contracts intentionally
# allow small legacy scalar fields (e.g., id/url), which normalization later
# drops. Reject nested, numerous, or oversized unused metadata.
_SOURCE_FIELDS = frozenset({"uri", "title", "content", "observed_at"})
_MAX_EXTRA_FIELDS = 4
_MAX_EXTRA_FIELD_NAME_CHARS = 64
_MAX_EXTRA_SCALAR_CHARS = 500


def validate_retrieved_evidence_bounds(
    sources: object, content: object,
) -> str | None:
    """Return a stable reason for oversized or unexpectedly shaped inputs.

    This does not establish provenance or semantic validity; later stages
    validate source URIs, scoped content consistency and timestamps.
    """
    if not isinstance(sources, (tuple, list)):
        return "invalid_sources"
    if len(sources) > MAX_RETRIEVED_SOURCES:
        return "too_many_sources"
    if content is not None and not isinstance(content, str):
        return "invalid_content"
    # For 0/1 sources, legacy combined content has a single-document limit.
    # Multiple source-scoped bodies can have at most 50k characters each.
    n = max(1, len(sources))
    max_content_chars = MAX_RETRIEVED_SOURCE_CONTENT_CHARS * n + 2 * (n - 1)
    if isinstance(content, str) and len(content) > max_content_chars:
        return "retrieved_content_too_large"

    for source in sources:
        if not isinstance(source, dict):
            return "invalid_sources"
        extra = set(source) - _SOURCE_FIELDS
        if len(extra) > _MAX_EXTRA_FIELDS:
            return "unexpected_source_metadata"
        for key in extra:
            value = source[key]
            if (
                not isinstance(key, str)
                or len(key) > _MAX_EXTRA_FIELD_NAME_CHARS
                or not isinstance(value, (str, int, float, bool))
                or len(str(value)) > _MAX_EXTRA_SCALAR_CHARS
            ):
                return "unexpected_source_metadata"
        uri: Any = source.get("uri")
        if isinstance(uri, str) and len(uri) > MAX_RETRIEVED_URI_CHARS:
            return "source_uri_too_long"
        title: Any = source.get("title")
        if isinstance(title, str) and len(title) > MAX_RETRIEVED_TITLE_CHARS:
            return "source_title_too_long"
        scoped_content: Any = source.get("content")
        if isinstance(scoped_content, str) and (
            len(scoped_content) > MAX_RETRIEVED_SOURCE_CONTENT_CHARS
        ):
            return "source_content_too_large"
        observed_at: Any = source.get("observed_at")
        if "observed_at" in source and (
            not isinstance(observed_at, str)
            or len(observed_at) > MAX_RETRIEVED_OBSERVED_AT_CHARS
        ):
            return "invalid_source_observed_at"
    return None


__all__ = [
    "MAX_RETRIEVED_SOURCES",
    "MAX_RETRIEVED_SOURCE_CONTENT_CHARS",
    "MAX_RETRIEVED_TITLE_CHARS",
    "MAX_RETRIEVED_URI_CHARS",
    "MAX_RETRIEVED_OBSERVED_AT_CHARS",
    "MAX_RETRIEVED_CLAIMS",
    "validate_retrieved_evidence_bounds",
]
