"""Fail-closed authenticated client: source first, real model only if warranted."""
from __future__ import annotations
from dataclasses import dataclass
from datetime import datetime,timezone,timedelta
from hashlib import sha256
from typing import Any,Literal
from backend.app.api.release_status import (
    ReleaseStatusSourceRequest,ReleaseStatusSourceResponse,release_status_binding
)
from backend.app.api.release_date import ReleaseDateSourceCitation
from backend.app.reality.release_status_policy import (
    status_question_valid,select_release_type_unit,normalize_model_release_type
)

PATH="/api/v1/reality-state/extract/release-status"
MAX_BYTES=8192

@dataclass(frozen=True)
class EvidenceConditionedReleaseStatus:
    outcome: Literal["bounded_source_release_type","abstain"]
    reason_code: Literal["model_matches_original_source","invalid_question",
                         "source_unavailable_or_invalid",
                         "model_unavailable_or_invalid","model_status_invalid_or_mismatched"]
    answer_type: str|None=None
    citation: ReleaseDateSourceCitation|None=None
    model_executed: bool=False
    may_use_as_bounded_evidence: bool=False
    factual_truth_verified: Literal[False]=False
    publisher_authorship_verified: Literal[False]=False
    general_question_answering: Literal[False]=False
    externally_deployed: Literal[False]=False

def _abstain(reason: str, executed: bool=False) -> EvidenceConditionedReleaseStatus:
    return EvidenceConditionedReleaseStatus("abstain",reason,model_executed=executed)

def validate_status_receipt(raw: object, req: ReleaseStatusSourceRequest) -> ReleaseDateSourceCitation|None:
    if type(raw) is not dict:
        return None
    for k in ("factual_truth_verified","publisher_authorship_verified",
              "model_used_for_source_verification","general_question_answering"):
        if type(raw.get(k)) is not bool or raw[k] is not False:
            return None
    if type(raw.get("original_source_observed")) is not bool:
        return None
    try:
        obj=ReleaseStatusSourceResponse.model_validate(raw)
        if (
            obj.outcome!="source_status_observed"
            or obj.reason_code!="stable_release_statement_observed"
            or obj.request_binding_sha256!=release_status_binding(req)
            or obj.original_source_observed is not True or obj.citation is None
        ):
            return None
        c=obj.citation
        if c.source_uri!=req.source_uri or c.original_source_quote!=c.original_source_quote.strip():
            return None
        if sha256(c.original_source_quote.encode("utf-8")).hexdigest()!=c.source_quote_sha256:
            return None
        if select_release_type_unit(req.entity+"\n"+c.original_source_quote,req.entity)!=c.original_source_quote:
            return None
        seen=datetime.fromisoformat(c.source_capture_observed_at.replace("Z","+00:00"))
        now=datetime.now(timezone.utc)
        if seen.tzinfo is None or seen>now+timedelta(seconds=30) or seen<now-timedelta(
            seconds=req.freshness_max_age_seconds
        ):
            return None
        return c
    except (ValueError,TypeError,OverflowError,AttributeError):
        return None

def check_release_status_with_model(
    client: Any,token: str,req: ReleaseStatusSourceRequest,model: Any
) -> EvidenceConditionedReleaseStatus:
    if not isinstance(req,ReleaseStatusSourceRequest) or not status_question_valid(
        req.question,req.entity,req.source_uri
    ):
        return _abstain("invalid_question")
    if type(token) is not str or not token.isascii() or not 32<=len(token)<=256 or any(
        ord(c)<33 or ord(c)>126 for c in token
    ):
        return _abstain("source_unavailable_or_invalid")
    if not callable(getattr(model,"extract_status",None)):
        return _abstain("model_unavailable_or_invalid")
    try:
        response=client.post(PATH,json=req.model_dump(mode="json"),headers={
            "Authorization":"Bearer "+token,"Accept":"application/json"
        })
        if (
            response.status_code!=200 or type(response.content) is not bytes
            or len(response.content)>MAX_BYTES
            or "application/json" not in response.headers.get("content-type","").lower()
        ):
            return _abstain("source_unavailable_or_invalid")
        c=validate_status_receipt(response.json(),req)
    except Exception:
        return _abstain("source_unavailable_or_invalid")
    if c is None:
        return _abstain("source_unavailable_or_invalid")
    try:
        proposed=model.extract_status(req.question,c.original_source_quote)
    except Exception:
        return _abstain("model_unavailable_or_invalid",True)
    if normalize_model_release_type(proposed)!="stable":
        return _abstain("model_status_invalid_or_mismatched",True)
    return EvidenceConditionedReleaseStatus(
        "bounded_source_release_type","model_matches_original_source",
        answer_type="stable",citation=c,model_executed=True,
        may_use_as_bounded_evidence=True
    )

__all__=["PATH","validate_status_receipt","EvidenceConditionedReleaseStatus",
         "check_release_status_with_model"]
