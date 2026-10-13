"""Step240: optional one-request, non-promoting neural *veto* for AI consumers.

This developer-facing adapter never chooses an API origin, retrieves a publisher,
installs a model, or executes actions. A trusted authenticated API supplies
a source-observed complete text unit. The original Step235 deterministic gate
MUST independently accept it BEFORE an injected NLI model may evaluate it.

Neural decisions can only *veto* an already-supported source claim. A neural
entailment cannot promote a source-abstained or contradicted claim to supported.
"""

from __future__ import annotations

from dataclasses import dataclass
from hashlib import sha256
import math
from typing import Any, Literal

from backend.app.api.original_source_claim import OriginalSourceClaimRequest
from backend.app.integrations.ai_claim_gate import (
    AIClaimGateDecision,
    CLAIM_PATH,
    MAX_API_RESPONSE_BYTES,
    _SHA,
    interpret_claim_reality_state,
)

_LABELS = frozenset({"entailment", "neutral", "contradiction"})


@dataclass(frozen=True)
class SemanticVetoDecision:
    decision: Literal["bounded_supported", "bounded_contradicted", "abstain"]
    may_use_as_bounded_evidence: bool
    reason_code: Literal[
        "source_not_supported", "source_bounded_contradiction",
        "missing_or_invalid_source_evidence", "neural_entailment_agrees",
        "neural_veto_nonentailment", "neural_unavailable_or_invalid",
        "api_unavailable_or_invalid",
    ]
    source_ref: str | None = None
    original_capture_sha256: str | None = None
    selected_text_sha256: str | None = None
    # Absolute epistemic limits; no caller can toggle them via model output.
    semantic_truth_verified: bool = False
    publisher_authorship_verified: bool = False
    neural_authorized_to_upgrade_claims: bool = False


def _refuse(reason: str = "neural_unavailable_or_invalid") -> SemanticVetoDecision:
    return SemanticVetoDecision("abstain", False, reason)


def _fetch_once(client: Any, token: str, request: OriginalSourceClaimRequest) -> object:
    if (
        not isinstance(token, str) or not token.isascii()
        or not 32 <= len(token) <= 256
        or any(ord(x) < 33 or ord(x) > 126 for x in token)
    ):
        return None
    try:
        reply = client.post(
            CLAIM_PATH,
            json=request.model_dump(mode="json"),
            headers={"Authorization": "Bearer " + token, "Accept": "application/json"},
        )
        raw = reply.content
        if (
            reply.status_code != 200
            or not isinstance(raw, bytes)
            or not 0 < len(raw) <= MAX_API_RESPONSE_BYTES
            or "application/json" not in reply.headers.get("content-type", "").lower()
        ):
            return None
        return reply.json()
    except Exception:
        return None


def _verified_source_text(
    data: object,
    decision: AIClaimGateDecision,
) -> tuple[str, str] | None:
    if (
        decision.decision != "bounded_supported"
        or decision.may_use_as_bounded_evidence is not True
        or not isinstance(data, dict)
    ):
        return None
    evidence = data.get("source_evidence")
    if not isinstance(evidence, dict) or set(evidence) != {
        "text", "text_sha256", "source_capture_sha256",
        "source_capture_observed_at",
    }:
        return None
    text, digest = evidence["text"], evidence["text_sha256"]
    if (
        not isinstance(text, str) or not 0 < len(text) <= 500
        or text != text.strip()
        or any(c in text for c in ("\n", "\r", "\x00"))
        or not isinstance(digest, str) or _SHA.fullmatch(digest) is None
        or sha256(text.encode("utf-8")).hexdigest() != digest
        or evidence["source_capture_sha256"] != decision.capture_sha256
        or evidence["source_capture_observed_at"] != decision.capture_observed_at
    ):
        return None
    return text, digest


def _valid_neural_result(response: object) -> str | None:
    if not isinstance(response, dict) or set(response) != {
        "predicted_relation", "uncalibrated_model_scores",
        "not_a_truth_probability", "not_authorized_to_support_claim",
    }:
        return None
    label = response["predicted_relation"]
    probs = response["uncalibrated_model_scores"]
    if (
        type(label) is not str or label not in _LABELS
        or response["not_a_truth_probability"] is not True
        or response["not_authorized_to_support_claim"] is not True
        or not isinstance(probs, dict) or set(probs) != _LABELS
        or any(
            type(x) not in (int, float) or not math.isfinite(x)
            or not 0 <= x <= 1 for x in probs.values()
        )
        or abs(sum(probs.values()) - 1.0) > 0.00001
        or probs[label] < max(probs.values())
    ):
        return None
    return label


def check_claim_with_semantic_veto(
    client: Any,
    token: str,
    request: OriginalSourceClaimRequest,
    *,
    model: Any,
) -> SemanticVetoDecision:
    """One original-source claim API call; NLI may only downgrade support.

    The caller owns API transport authenticity/TLS, secret storage, model
    initialization and any use of this developer-facing result. No second
    publisher network read or additional model acquisition is performed here.
    """
    if not isinstance(request, OriginalSourceClaimRequest):
        raise TypeError("request must be a validated OriginalSourceClaimRequest")
    data = _fetch_once(client, token, request)
    if not isinstance(data, dict):
        return _refuse("api_unavailable_or_invalid")
    original = interpret_claim_reality_state(data, request)
    if original.decision == "abstain":
        return _refuse("source_not_supported")
    if original.decision == "bounded_contradicted":
        return SemanticVetoDecision(
            "bounded_contradicted", False, "source_bounded_contradiction",
            original.source_ref, original.capture_sha256,
        )
    verified = _verified_source_text(data, original)
    if verified is None:
        return _refuse("missing_or_invalid_source_evidence")
    text, digest = verified
    if not callable(getattr(model, "predict", None)):
        return _refuse()
    try:
        result = model.predict(text, request.claim_text)
    except Exception:
        return _refuse()
    label = _valid_neural_result(result)
    if label is None:
        return _refuse()
    if label != "entailment":
        return SemanticVetoDecision(
            "abstain", False, "neural_veto_nonentailment",
            original.source_ref, original.capture_sha256, digest,
        )
    return SemanticVetoDecision(
        "bounded_supported", True, "neural_entailment_agrees",
        original.source_ref, original.capture_sha256, digest,
    )


__all__ = ["SemanticVetoDecision", "check_claim_with_semantic_veto"]
