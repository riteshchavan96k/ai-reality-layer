"""Step255 exact-entity source routing + zero-neural direct verified-source answers.

The API intentionally supports only Python X.Y.Z historical release date and
stable release TYPE; this is not current security support and not open web
search. The authoritative evidence readers remain Steps253/254, one capture.
"""
from __future__ import annotations

import re

from backend.app.api.evidence_first_ask import (
    EvidenceFirstAskRequest, EvidenceFirstAskResponse, ask_request_binding,
)
from backend.app.api.release_date import ReleaseDateSourceRequest
from backend.app.api.release_status import ReleaseStatusSourceRequest
from backend.app.reality.release_date_policy import (
    expected_question, parse_release_date_label,
)
from backend.app.reality.release_status_policy import (
    status_question_valid, select_release_type_unit,
)
from backend.app.services.release_date_source_service import observe_release_date
from backend.app.services.release_status_source_service import observe_release_status

_VERSION = re.compile(r"Python ([0-9]+)\.([0-9]+)\.([0-9]+)\Z")


def resolved_question(request: EvidenceFirstAskRequest) -> tuple[str, str] | None:
    """Resolve only exact syntactic domain identity: never general URL search."""
    if not isinstance(request, EvidenceFirstAskRequest):
        return None
    match = _VERSION.fullmatch(request.entity)
    if match is None or request.entity != request.entity.strip():
        return None
    major, minor, micro = map(int, match.groups())
    if not (2 <= major <= 9 and 0 <= minor <= 99 and 0 <= micro <= 9):
        return None
    url = f"https://www.python.org/downloads/release/python-{major}{minor}{micro}/"
    if expected_question(request.question, request.entity, url):
        return "release_date", url
    if status_question_valid(request.question, request.entity, url):
        return "release_type", url
    return None


def ask_evidence_first(request: EvidenceFirstAskRequest) -> EvidenceFirstAskResponse:
    if not isinstance(request, EvidenceFirstAskRequest):
        raise TypeError("validated_request_required")
    binding = ask_request_binding(request)

    def abstain(reason: str) -> EvidenceFirstAskResponse:
        return EvidenceFirstAskResponse(
            outcome="abstain", reason_code=reason, request_binding_sha256=binding
        )

    scope = resolved_question(request)
    if scope is None:
        return abstain("unsupported_question")
    kind, source_uri = scope
    if kind == "release_date":
        source_request = ReleaseDateSourceRequest(
            question=request.question, entity=request.entity, source_uri=source_uri,
            freshness_max_age_seconds=request.freshness_max_age_seconds,
        )
        observed = observe_release_date(source_request)
        if observed.outcome != "source_date_observed" or observed.citation is None:
            return abstain(
                "source_not_operator_allowed" if observed.reason_code
                == "source_not_operator_allowed" else "source_unavailable_or_ambiguous"
            )
        date = parse_release_date_label(observed.citation.original_source_quote)
        if date is None:
            return abstain("source_unavailable_or_ambiguous")
        answer_value = date.isoformat()
    else:
        source_request = ReleaseStatusSourceRequest(
            question=request.question, entity=request.entity, source_uri=source_uri,
            freshness_max_age_seconds=request.freshness_max_age_seconds,
        )
        observed = observe_release_status(source_request)
        if observed.outcome != "source_status_observed" or observed.citation is None:
            return abstain(
                "source_not_operator_allowed" if observed.reason_code
                == "source_not_operator_allowed" else "source_unavailable_or_ambiguous"
            )
        unit = observed.citation.original_source_quote
        if select_release_type_unit(request.entity + "\n" + unit, request.entity) != unit:
            return abstain("source_unavailable_or_ambiguous")
        answer_value = "stable"
    # No model invocation, no second source read, and no caller supplied URL.
    return EvidenceFirstAskResponse(
        outcome="bounded_source_answer",
        reason_code="independent_original_source_answer",
        request_binding_sha256=binding,
        source_request_binding_sha256=observed.request_binding_sha256,
        entity=request.entity,
        fact_kind=kind,
        answer_value=answer_value,
        citation=observed.citation,
        observed_source_support=True,
    )


__all__ = ["resolved_question", "ask_evidence_first"]
