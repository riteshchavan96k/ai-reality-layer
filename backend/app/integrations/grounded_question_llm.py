"""Step252: opt-in question -> real LLM proposal -> independently cited source gate.

This is a local/developer callable adapter, not a public model endpoint.
Only a *bounded yes/no question* is allowed. A model cannot silently change
the entity, requested predicate, property, or negation, and cannot supply
citations, source text, policy flags or the final answer. No model output
may expand the original Step241/242 verified evidence permission.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Literal

from backend.app.api.original_source_claim import OriginalSourceClaimRequest
from backend.app.integrations.cited_answer_client import (
    CitedSourceObservation, check_cited_answer_with_api,
)
from backend.app.reality.claim_assertion_alignment import _parse_atomic


@dataclass(frozen=True)
class GroundedLLMQuestionResult:
    outcome: Literal["bounded_source_support", "bounded_source_contradiction", "abstain"]
    reason_code: Literal[
        "source_aligned", "source_contradicted", "source_abstained",
        "invalid_question", "model_unavailable_or_invalid",
        "generated_claim_drift", "api_unavailable_or_invalid",
    ]
    claim_text: str | None = None
    citation: CitedSourceObservation | None = None
    may_use_as_bounded_evidence: bool = False
    llm_generated_candidate: bool = False
    factual_truth_verified: Literal[False] = False
    publisher_authorship_verified: Literal[False] = False
    general_question_answering: Literal[False] = False
    externally_deployed: Literal[False] = False


def _refuse(reason: str, *, generated: bool = False) -> GroundedLLMQuestionResult:
    return GroundedLLMQuestionResult(
        "abstain", reason, llm_generated_candidate=generated
    )


def _expected_atomic_question(question: str, entity: str) -> str | None:
    """Bind a yes/no question to an exact parsed atomic hypothesis.

    Do NOT infer question intent with another model or accept arbitrary
    generative paraphrases. This deliberately abstains on most real questions.
    """
    if (
        type(question) is not str or not 0 < len(question) <= 300
        or question != question.strip() or question.count("?") != 1
        or not question.endswith("?") or any(c in question for c in "\r\n\x00")
        or type(entity) is not str or not 0 < len(entity) <= 100
    ):
        return None
    for interrogative, verb in (("Is ", "is"), ("Was ", "was")):
        prefix = interrogative + entity + " "
        if question[:len(prefix)].casefold() != prefix.casefold():
            continue
        property_text = question[len(prefix):-1]
        if (
            not property_text or property_text != property_text.strip()
            or len(property_text) > 100
        ):
            return None
        expected = entity + " " + verb + " " + property_text + "."
        parsed = _parse_atomic(expected)
        if parsed is not None and parsed[0] == " ".join(entity.split()).casefold():
            return expected
    return None


def check_question_with_grounded_llm(
    client: Any, token: str, question: str, *,
    entity: str, source_uri: str, model: Any,
    freshness_max_age_seconds: float = 3600.0,
) -> GroundedLLMQuestionResult:
    """One bounded generative proposal, then at most ONE authorized source GET.

    Model generation receives ONLY the bounded user question, NEVER raw
    publisher content or bearer. The model's proposed claim is first tied to
    the user's exact predicate and polarity, then checked against the real
    original-source evidence with the existing Step242 defensive API client.
    """
    expected = _expected_atomic_question(question, entity)
    if expected is None:
        return _refuse("invalid_question")
    try:
        # Server still decides whether this is an operator-allowlisted source.
        # Validation before model generation denies malformed or unsafe URLs.
        preflight = OriginalSourceClaimRequest(
            claim_text=expected, entity=entity, source_uri=source_uri,
            freshness_max_age_seconds=freshness_max_age_seconds,
        )
    except (TypeError, ValueError):
        return _refuse("invalid_question")
    if not callable(getattr(model, "propose", None)):
        return _refuse("model_unavailable_or_invalid")
    try:
        proposal = model.propose(question)
    except Exception:
        return _refuse("model_unavailable_or_invalid")
    if (
        type(proposal) is not str or not 0 < len(proposal) <= 500
        or proposal != proposal.strip()
        or any(c in proposal for c in "\r\n\x00")
        or _parse_atomic(proposal) != _parse_atomic(preflight.claim_text)
    ):
        return _refuse("generated_claim_drift", generated=True)
    try:
        request = OriginalSourceClaimRequest(
            claim_text=proposal, entity=entity, source_uri=source_uri,
            freshness_max_age_seconds=freshness_max_age_seconds,
        )
        verified = check_cited_answer_with_api(client, token, request)
    except Exception:
        return _refuse("api_unavailable_or_invalid", generated=True)
    if verified.decision == "abstain" or verified.citation is None:
        return _refuse(
            "source_abstained" if verified.reason_code == "source_abstained"
            else "api_unavailable_or_invalid",
            generated=True,
        )
    if verified.decision not in (
        "bounded_source_support", "bounded_source_contradiction"
    ):
        return _refuse("api_unavailable_or_invalid", generated=True)
    # The lower layer already independently validates request-binding digest,
    # source quote/capture hashes, observation freshness and epistemic flags.
    if verified.factual_truth_verified is not False or verified.publisher_authorship_verified is not False:
        return _refuse("api_unavailable_or_invalid", generated=True)
    supported = verified.decision == "bounded_source_support"
    return GroundedLLMQuestionResult(
        outcome=verified.decision,
        reason_code="source_aligned" if supported else "source_contradicted",
        claim_text=proposal,
        citation=verified.citation,
        may_use_as_bounded_evidence=supported,
        llm_generated_candidate=True,
    )


__all__ = [
    "GroundedLLMQuestionResult", "check_question_with_grounded_llm",
]
