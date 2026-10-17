"""Step254 exact official source evidence for historical Python release type."""
from __future__ import annotations
from hashlib import sha256
import json
from typing import Literal
from pydantic import BaseModel, ConfigDict, Field
from backend.app.api.release_date import ReleaseDateSourceRequest, ReleaseDateSourceCitation

class ReleaseStatusSourceRequest(ReleaseDateSourceRequest):
    """Same safe URL/freshness schema as Step253, distinct semantic request."""

def release_status_binding(request: ReleaseStatusSourceRequest) -> str:
    if not isinstance(request,ReleaseStatusSourceRequest):
        raise TypeError("invalid_status_request")
    body=json.dumps(request.model_dump(mode="json"),sort_keys=True,
                    separators=(",",":"),ensure_ascii=True,
                    allow_nan=False).encode("utf-8")
    return sha256(b"arl-step254-status-v1:"+body).hexdigest()

class ReleaseStatusSourceResponse(BaseModel):
    model_config=ConfigDict(extra="forbid")
    outcome: Literal["source_status_observed","abstain"]
    reason_code: Literal["stable_release_statement_observed","invalid_question_or_identity",
                         "source_not_operator_allowed","source_unavailable",
                         "source_ambiguous_or_unverified","source_capture_invalid"]
    request_binding_sha256: str=Field(pattern=r"^[0-9a-f]{64}$")
    citation: ReleaseDateSourceCitation|None=None
    original_source_observed: bool=False
    factual_truth_verified: Literal[False]=False
    publisher_authorship_verified: Literal[False]=False
    model_used_for_source_verification: Literal[False]=False
    general_question_answering: Literal[False]=False

__all__=["ReleaseStatusSourceRequest","ReleaseStatusSourceResponse","release_status_binding"]
