"""Two separately observed, distinct-host bounded source-answer contract.

Distinct hostnames DO NOT prove independent publishers or factual truth.
"""
import json
from hashlib import sha256
from urllib.parse import urlsplit
from typing import Literal
from pydantic import BaseModel, ConfigDict, Field, model_validator
from backend.app.api.original_source_answer import ObservedAnswerCitation
from backend.app.api.original_source_claim import OriginalSourceClaimRequest

class TwoOriginAnswerRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")
    claim_text: str = Field(min_length=1, max_length=500)
    entity: str = Field(min_length=1, max_length=150)
    source_uris: list[str] = Field(min_length=2, max_length=2)
    freshness_max_age_seconds: float | int = 3600

    @model_validator(mode="after")
    def checked_pair(self):
        requests = [OriginalSourceClaimRequest(
            claim_text=self.claim_text, entity=self.entity,
            source_uri=uri, freshness_max_age_seconds=self.freshness_max_age_seconds
        ) for uri in self.source_uris]
        hosts = [urlsplit(req.source_uri).hostname for req in requests]
        if any(host is None for host in hosts) or hosts[0].rstrip(".").casefold() == hosts[1].rstrip(".").casefold():
            raise ValueError("two distinct HTTPS hostnames are required")
        self.claim_text = requests[0].claim_text
        self.entity = requests[0].entity
        self.source_uris = [req.source_uri for req in requests]
        self.freshness_max_age_seconds = requests[0].freshness_max_age_seconds
        return self

    def source_requests(self) -> tuple[OriginalSourceClaimRequest, OriginalSourceClaimRequest]:
        return tuple(OriginalSourceClaimRequest(
            claim_text=self.claim_text, entity=self.entity,
            source_uri=uri, freshness_max_age_seconds=self.freshness_max_age_seconds,
        ) for uri in self.source_uris)

def two_origin_binding_sha256(request: TwoOriginAnswerRequest) -> str:
    if not isinstance(request, TwoOriginAnswerRequest):
        raise TypeError("validated two-origin request required")
    data = {"contract": "two-host-cited-answer-step243-v1",
            "request": request.model_dump(mode="json")}
    canonical = json.dumps(data, sort_keys=True, separators=(",", ":"),
                           ensure_ascii=True, allow_nan=False).encode("utf-8")
    return sha256(canonical).hexdigest()

PAIR_ALIGNED = ("Both separately observed HTTPS source statements align with the "
                "submitted claim under a bounded textual verification policy.")
PAIR_CONTRADICTED = ("Both separately observed HTTPS source statements contradict "
                     "the submitted claim under a bounded textual verification policy.")
PAIR_DISAGREEMENT = ("The two separately observed HTTPS source statements disagree "
                     "about the submitted claim under a bounded textual verification policy.")
PAIR_ABSTAINED = ("Both required original-source observations could not be verified "
                  "for a bounded two-source answer.")

class TwoOriginAnswerResponse(BaseModel):
    model_config = ConfigDict(extra="forbid")
    outcome: Literal["two_source_alignment", "two_source_contradiction", "source_disagreement", "abstain"]
    answer_text: Literal[PAIR_ALIGNED, PAIR_CONTRADICTED, PAIR_DISAGREEMENT, PAIR_ABSTAINED]
    reason_code: Literal["two_source_aligned", "two_source_contradicted",
                         "two_source_disagreement", "source_evidence_incomplete"]
    request_binding_sha256: str = Field(pattern=r"^[a-f0-9]{64}$")
    citations: list[ObservedAnswerCitation] = Field(default_factory=list, max_length=2)
    source_observation_count: Literal[0, 2] = 0
    distinct_https_hostnames: bool = False
    may_use_as_bounded_evidence: bool = False
    factual_truth_verified: Literal[False] = False
    publisher_authorship_verified: Literal[False] = False
    independently_owned_publishers_verified: Literal[False] = False
    neural_model_used: Literal[False] = False
    general_question_answering: Literal[False] = False
