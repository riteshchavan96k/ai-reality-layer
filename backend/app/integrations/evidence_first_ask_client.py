"""Step255 defensive consumer: original source answers, model optional only.

This client treats the authenticated HTTPS transport as trusted. Source hashes
are integrity check identifiers, not publisher signatures or transport auth.
No LLM may replace the independent original-source answer or attribution.
"""
from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from hashlib import sha256
from typing import Any, Literal

from backend.app.api.evidence_first_ask import (
    EvidenceFirstAskRequest, EvidenceFirstAskResponse, ask_request_binding,
)
from backend.app.api.release_date import (
    ReleaseDateSourceRequest, ReleaseDateSourceCitation,
)
from backend.app.api.claim_request_binding import claim_request_binding_sha256
from backend.app.api.release_status import (
    ReleaseStatusSourceRequest, release_status_binding,
)
from backend.app.reality.release_date_policy import parse_release_date_label
from backend.app.reality.release_status_policy import (
    select_release_type_unit, normalize_model_release_type,
)
from backend.app.services.evidence_first_ask_service import resolved_question

PATH="/api/v1/reality-state/ask"
MAX_BYTES=8192


@dataclass(frozen=True)
class EvidenceFirstDeveloperAnswer:
    outcome: Literal["bounded_source_answer","abstain"]
    reason_code: Literal[
        "independent_original_source_answer","invalid_question",
        "source_unavailable_or_invalid",
    ]
    answer_value: str|None=None
    fact_kind: Literal["release_date","release_type"]|None=None
    citation: ReleaseDateSourceCitation|None=None
    optional_model_assessment: Literal[
        "not_requested","model_agrees","model_disagrees","model_unavailable"
    ]="not_requested"
    may_use_as_bounded_evidence: bool=False
    factual_truth_verified: Literal[False]=False
    publisher_authorship_verified: Literal[False]=False
    general_question_answering: Literal[False]=False
    externally_deployed: Literal[False]=False


def _abstain(reason: str) -> EvidenceFirstDeveloperAnswer:
    return EvidenceFirstDeveloperAnswer("abstain",reason)


def _receipt(raw: object, request: EvidenceFirstAskRequest) -> EvidenceFirstAskResponse|None:
    if type(raw) is not dict:
        return None
    for k in ("model_executed","factual_truth_verified","publisher_authorship_verified",
              "general_question_answering","externally_deployed"):
        if type(raw.get(k)) is not bool or raw[k] is not False:
            return None
    if type(raw.get("observed_source_support")) is not bool:
        return None
    scope=resolved_question(request)
    if scope is None:
        return None
    kind,url=scope
    try:
        response=EvidenceFirstAskResponse.model_validate(raw)
        if (
            response.outcome!="bounded_source_answer"
            or response.reason_code!="independent_original_source_answer"
            or response.request_binding_sha256!=ask_request_binding(request)
            or response.observed_source_support is not True
            or response.fact_kind!=kind or response.entity!=request.entity
            or response.citation is None or response.source_request_binding_sha256 is None
        ):
            return None
        cite=response.citation
        if cite.source_uri!=url or cite.original_source_quote!=cite.original_source_quote.strip():
            return None
        if sha256(cite.original_source_quote.encode("utf-8")).hexdigest()!=cite.source_quote_sha256:
            return None
        seen=datetime.fromisoformat(cite.source_capture_observed_at.replace("Z","+00:00"))
        now=datetime.now(timezone.utc)
        if (
            seen.tzinfo is None
            or seen>now+timedelta(seconds=30)
            or seen<now-timedelta(seconds=request.freshness_max_age_seconds)
        ):
            return None
        if kind=="release_date":
            sub=ReleaseDateSourceRequest(
                question=request.question,entity=request.entity,source_uri=url,
                freshness_max_age_seconds=request.freshness_max_age_seconds
            )
            from backend.app.api.claim_request_binding import claim_request_binding_sha256
            # Existing Step253 hash is the SHA256 of a canonical source
            # request, with no separate domain prefix (same as source claim).
            from hashlib import sha256 as _sha256
            import json
            original=json.dumps(sub.model_dump(mode="json"),sort_keys=True,
                                separators=(",",":"),ensure_ascii=True,
                                allow_nan=False).encode("utf-8")
            expected=_sha256(original).hexdigest()
            date=parse_release_date_label(cite.original_source_quote)
            if date is None or response.answer_value!=date.isoformat() or date>now.date():
                return None
        else:
            sub=ReleaseStatusSourceRequest(
                question=request.question,entity=request.entity,source_uri=url,
                freshness_max_age_seconds=request.freshness_max_age_seconds
            )
            expected=release_status_binding(sub)
            if (
                select_release_type_unit(
                    request.entity+"\n"+cite.original_source_quote,request.entity
                )!=cite.original_source_quote
                or response.answer_value!="stable"
            ):
                return None
        if response.source_request_binding_sha256!=expected:
            return None
        return response
    except (TypeError,ValueError,OverflowError,AttributeError):
        return None


def ask_with_optional_model(
    client: Any,token: str,request: EvidenceFirstAskRequest,
    *,model: Any|None=None
) -> EvidenceFirstDeveloperAnswer:
    if not isinstance(request,EvidenceFirstAskRequest) or resolved_question(request) is None:
        return _abstain("invalid_question")
    if (type(token) is not str or not token.isascii()
        or not 32<=len(token)<=256 or any(ord(c)<33 or ord(c)>126 for c in token)):
        return _abstain("source_unavailable_or_invalid")
    try:
        response=client.post(
            PATH,json=request.model_dump(mode="json"),
            headers={"Authorization":"Bearer "+token,"Accept":"application/json"}
        )
        if (response.status_code!=200 or type(response.content) is not bytes
            or len(response.content)>MAX_BYTES
            or "application/json" not in response.headers.get("content-type","").lower()):
            return _abstain("source_unavailable_or_invalid")
        verified=_receipt(response.json(),request)
    except Exception:
        return _abstain("source_unavailable_or_invalid")
    if verified is None:
        return _abstain("source_unavailable_or_invalid")

    assessment="not_requested"
    if model is not None:
        try:
            if verified.fact_kind=="release_date":
                result=model.extract_date(request.question,
                                          verified.citation.original_source_quote)
                from backend.app.reality.release_date_policy import parse_date
                prediction=parse_date(result)
                matches=prediction is not None and prediction.isoformat()==verified.answer_value
            else:
                result=model.extract_status(request.question,
                                            verified.citation.original_source_quote)
                matches=normalize_model_release_type(result)==verified.answer_value
            assessment="model_agrees" if matches else "model_disagrees"
        except Exception:
            assessment="model_unavailable"
    # Model result is separate diagnostic only. It cannot create, hide,
    # downgrade or change any already-verified original-source answer.
    return EvidenceFirstDeveloperAnswer(
        outcome="bounded_source_answer",
        reason_code="independent_original_source_answer",
        answer_value=verified.answer_value,fact_kind=verified.fact_kind,
        citation=verified.citation,may_use_as_bounded_evidence=True,
        optional_model_assessment=assessment,
    )


__all__=["PATH","EvidenceFirstDeveloperAnswer","ask_with_optional_model"]
