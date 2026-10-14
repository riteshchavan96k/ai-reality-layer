"""Two-host original-source cited answer; independently verify BOTH existing one-source checks."""
from dataclasses import asdict
from backend.app.api.original_source_answer import ObservedAnswerCitation
from backend.app.api.two_origin_answer import (
    TwoOriginAnswerRequest, TwoOriginAnswerResponse, two_origin_binding_sha256,
    PAIR_ALIGNED, PAIR_CONTRADICTED, PAIR_DISAGREEMENT, PAIR_ABSTAINED,
)
from backend.app.integrations.cited_answer_client import interpret_cited_answer
from backend.app.orchestrator.dependencies import OrchestrationDependencies
from backend.app.reality.allowlisted_https_source_reader import AllowlistedHttpsSourceReader
from backend.app.services.original_source_answer_service import answer_original_source_claim

def _abstain(request: TwoOriginAnswerRequest) -> TwoOriginAnswerResponse:
    return TwoOriginAnswerResponse(
        outcome="abstain", reason_code="source_evidence_incomplete",
        answer_text=PAIR_ABSTAINED, request_binding_sha256=two_origin_binding_sha256(request),
    )

def answer_two_distinct_https_origins(request: TwoOriginAnswerRequest) -> TwoOriginAnswerResponse:
    """At most one source read per URL, never expose partially verified receipts.

    A hostile second URL is denied BEFORE making any first-source request.
    Distinct hostname is not proof of two independent publisher owners.
    """
    if not isinstance(request, TwoOriginAnswerRequest):
        raise TypeError("validated request required")
    try:
        singles = request.source_requests()
        reader = OrchestrationDependencies.default().independent_source_text_assurance._reader
        if not isinstance(reader, AllowlistedHttpsSourceReader) or any(
            one.source_uri not in reader._allowed for one in singles
        ):
            return _abstain(request)
        observations = []
        for single in singles:
            reply = answer_original_source_claim(single)
            checked = interpret_cited_answer(reply.model_dump(mode="json"), single)
            if checked.decision not in (
                "bounded_source_support", "bounded_source_contradiction"
            ) or checked.citation is None or checked.citation.source_uri != single.source_uri:
                return _abstain(request)
            observations.append(checked)
        if len(observations) != 2:
            return _abstain(request)
        directions = tuple(item.decision for item in observations)
        if directions == ("bounded_source_support", "bounded_source_support"):
            outcome, reason, statement, may_use = (
                "two_source_alignment", "two_source_aligned", PAIR_ALIGNED, True,
            )
        elif directions == ("bounded_source_contradiction", "bounded_source_contradiction"):
            outcome, reason, statement, may_use = (
                "two_source_contradiction", "two_source_contradicted", PAIR_CONTRADICTED, False,
            )
        else:
            outcome, reason, statement, may_use = (
                "source_disagreement", "two_source_disagreement", PAIR_DISAGREEMENT, False,
            )
        return TwoOriginAnswerResponse(
            outcome=outcome, reason_code=reason, answer_text=statement,
            request_binding_sha256=two_origin_binding_sha256(request),
            citations=[ObservedAnswerCitation.model_validate(asdict(item.citation))
                       for item in observations],
            source_observation_count=2, distinct_https_hostnames=True,
            may_use_as_bounded_evidence=may_use,
        )
    except Exception:
        return _abstain(request)
