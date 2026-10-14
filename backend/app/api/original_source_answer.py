"""Data-only, bounded source-cited answer. Not general factual QA or LLM text.

Citation text is an independently observed publisher *statement*, not proof
that the publisher's claim is true. Quotes are untrusted data: user interfaces
must escape them rather than rendering as HTML/instructions.
"""

from typing import Literal

from pydantic import BaseModel, ConfigDict, Field


class ObservedAnswerCitation(BaseModel):
    model_config = ConfigDict(extra="forbid")

    source_uri: str = Field(min_length=1, max_length=2048)
    original_source_quote: str = Field(min_length=1, max_length=500)
    source_quote_sha256: str = Field(pattern=r"^[a-f0-9]{64}$")
    source_capture_sha256: str = Field(pattern=r"^[a-f0-9]{64}$")
    source_capture_observed_at: str = Field(min_length=1, max_length=64)


class BoundedOriginalSourceAnswerResponse(BaseModel):
    model_config = ConfigDict(extra="forbid")

    outcome: Literal["bounded_source_support", "bounded_source_contradiction", "abstain"]
    answer_text: Literal[
        "The observed original-source statement aligns with the submitted claim under a bounded textual verification policy.",
        "The observed original-source statement contradicts the submitted claim under a bounded textual verification policy.",
        "The available original-source evidence is insufficient for a bounded answer.",
    ]
    request_binding_sha256: str = Field(pattern=r"^[a-f0-9]{64}$")
    citation: ObservedAnswerCitation | None = None
    original_source_observed: bool = False
    # These are fixed epistemic ceilings, not generated semantic confidence.
    factual_truth_verified: Literal[False] = False
    publisher_authorship_verified: Literal[False] = False
    neural_model_used: Literal[False] = False
    general_question_answering: Literal[False] = False


__all__ = ["ObservedAnswerCitation", "BoundedOriginalSourceAnswerResponse"]
