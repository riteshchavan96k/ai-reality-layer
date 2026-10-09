"""Optional, server-side exact-text assurance for independently read source bytes.

Caller-supplied URLs, observation timestamps, hashes and claims are NEVER
attestations. Only a backend-installed reader can provide comparison text.
The match proves exact substring presence *in the reader's returned bytes*,
not original publisher authorship, semantic entailment or truth.
"""

from collections.abc import Callable, Mapping
from hashlib import sha256
from typing import Any

from backend.app.reality.submitted_evidence import SubmittedEvidenceBundle


MAX_INDEPENDENT_SOURCE_TEXT_CHARS = 200_000
SourceTextReader = Callable[[str], Mapping[str, Any]]


class IndependentSourceTextAssurance:
    """Compare a complete supplied excerpt to a separately read document."""

    def __init__(self, reader: SourceTextReader | None = None) -> None:
        if reader is not None and not callable(reader):
            raise ValueError("independent source reader must be callable or None")
        self._reader = reader

    def check(self, bundle: SubmittedEvidenceBundle) -> dict[str, Any]:
        if not isinstance(bundle, SubmittedEvidenceBundle):
            raise ValueError("bundle must be a SubmittedEvidenceBundle")

        # Each source gets an auditable decision. Never accept flags provided
        # by the API caller or invent observed bytes when unconfigured.
        items: list[dict[str, Any]] = []
        for doc in bundle.documents:
            outcome: dict[str, Any] = {
                "source_ref": doc.uri,
                "status": "unverified",
                "reason": "independent_reader_unconfigured",
                "observer_content_sha256": None,
            }
            if self._reader is not None:
                try:
                    observed = self._reader(doc.uri)
                    if not isinstance(observed, Mapping):
                        outcome["reason"] = "invalid_observer_response"
                    elif observed.get("uri") != doc.uri:
                        outcome["reason"] = "observer_source_identity_mismatch"
                    else:
                        body = observed.get("content")
                        if not isinstance(body, str) or not body:
                            outcome["reason"] = "invalid_observer_content"
                        elif len(body) > MAX_INDEPENDENT_SOURCE_TEXT_CHARS:
                            outcome["reason"] = "observer_content_over_limit"
                        elif doc.content.strip() not in body:
                            outcome["reason"] = "submitted_text_not_in_observed_content"
                        else:
                            outcome["status"] = "exact_text_observed"
                            outcome["reason"] = None
                            # Identifies reader-supplied comparison content;
                            # an untrusted digest alone proves no provenance.
                            outcome["observer_content_sha256"] = sha256(
                                body.encode("utf-8")
                            ).hexdigest()
                except Exception:
                    # Never disclose exceptions from a backend-configured
                    # provider in a public response.
                    outcome["reason"] = "observer_unavailable"
            items.append(outcome)

        all_matched = all(
            item["status"] == "exact_text_observed" for item in items
        )
        return {
            "status": "exact_text_observed" if all_matched else "unverified",
            "verification_method": "server_controlled_reader_exact_substring",
            "sources": items,
            "source_count": len(items),
            "matched_source_count": sum(
                item["status"] == "exact_text_observed" for item in items
            ),
            "publisher_authenticated": False,
            "semantic_support_verified": False,
        }


__all__ = [
    "MAX_INDEPENDENT_SOURCE_TEXT_CHARS",
    "SourceTextReader",
    "IndependentSourceTextAssurance",
]
