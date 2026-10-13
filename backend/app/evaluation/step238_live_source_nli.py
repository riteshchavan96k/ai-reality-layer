"""Step238: one genuine original-source HTTPS capture -> real neural NLI shadow.

Research tool only; never import this from production FastAPI or claim services.
A TLS-verified original-source observation supplies the *premise* but still
cannot prove world truth, independent publisher endorsement, or general model
accuracy. Neither the model nor this report can authorize Reality State support.
"""

from __future__ import annotations

import argparse
from datetime import datetime, timedelta, timezone
from hashlib import sha256
import json
import math
from pathlib import Path
import re
from typing import Any

from backend.app.reality.allowlisted_https_source_reader import AllowlistedHttpsSourceReader
from backend.app.reality.claim_assertion_alignment import _parse_atomic, _relationship
from backend.app.reality.independent_source_text_assurance import MAX_INDEPENDENT_SOURCE_TEXT_CHARS
from backend.app.evaluation.step237_nli_shadow import (
    EXPECTED_LABELS, MODEL_REPO, MODEL_REVISION, ONNX_SHA256,
    load_reviewed_model,
)

SOURCE = "https://www.python.org/downloads/release/python-3130/"
STANDALONE_ANCHOR = "This is the stable release of Python 3.13.0"
MAX_CAPTURE_AGE_SECONDS = 3600
MAX_FUTURE_SECONDS = 30
MAX_STANDALONE_UNIT_CHARS = 500
RECEIPT = re.compile(r"[0-9a-f]{64}")

# All candidate claims are developer-authored; do not invent gold labels.
# One independent source capture will be reused for each inference.
CLAIMS = (
    ("source_direct", "Python 3.13.0 is a stable release."),
    ("source_negated", "Python 3.13.0 is not a stable release."),
    ("source_paraphrase", "Python 3.13.0 is a production-ready release."),
)


class ObservedNLIError(ValueError):
    """Fixed, secret-free source or model policy failure."""


def _require(ok: bool, reason: str) -> None:
    if not ok:
        raise ObservedNLIError(reason)


def select_standalone_observed_unit(
    observation: object,
    *, now: datetime | None = None,
) -> dict[str, str]:
    """Refuse any source other than one fresh, unquoted complete text unit.

    The real reader internally hashes *raw HTTP bytes*, not rendered HTML; a
    captured SHA cannot be recomputed from the rendered excerpt. It is a
    receipt from the trusted reader, not a cryptographic publisher signature.
    """
    _require(type(observation) is dict, "source_observation_invalid")
    observed: dict[str, Any] = observation
    _require(observed.get("uri") == SOURCE, "original_source_identity_mismatch")
    body = observed.get("content")
    receipt = observed.get("capture_sha256")
    captured_at = observed.get("capture_observed_at")
    quote_hashes = observed.get("observed_quote_unit_sha256")
    _require(type(body) is str and 0 < len(body) <= MAX_INDEPENDENT_SOURCE_TEXT_CHARS,
             "source_body_invalid")
    _require(type(receipt) is str and RECEIPT.fullmatch(receipt) is not None,
             "source_receipt_invalid")
    _require(type(captured_at) is str and captured_at.endswith("Z"),
             "source_capture_time_invalid")
    _require(type(quote_hashes) in (list, tuple)
             and len(quote_hashes) <= 128 and all(
                 type(item) is str and RECEIPT.fullmatch(item) is not None
                 for item in quote_hashes
             ) and len(set(quote_hashes)) == len(quote_hashes),
             "source_quotation_receipts_invalid")

    current = datetime.now(timezone.utc) if now is None else now
    _require(isinstance(current, datetime) and current.tzinfo is not None,
             "clock_invalid")
    try:
        timestamp = datetime.fromisoformat(captured_at.replace("Z", "+00:00"))
    except (TypeError, ValueError, OverflowError):
        raise ObservedNLIError("source_capture_time_invalid") from None
    _require(timestamp.tzinfo is not None
             and timestamp <= current + timedelta(seconds=MAX_FUTURE_SECONDS)
             and timestamp >= current - timedelta(seconds=MAX_CAPTURE_AGE_SECONDS),
             "source_capture_not_fresh")

    # The full HTML visible-text unit must be exactly the operator-reviewed
    # assertion anchor. Never select a substring from a longer/quoted unit.
    lines = [line.strip() for line in body.split("\n")]
    matched = [line for line in lines if line == STANDALONE_ANCHOR]
    _require(len(matched) == 1, "source_unit_not_unique_or_missing")
    chosen = matched[0]
    _require(0 < len(chosen) <= MAX_STANDALONE_UNIT_CHARS,
             "source_unit_invalid")
    unit_hash = sha256(" ".join(chosen.split()).encode("utf-8")).hexdigest()
    _require(unit_hash not in quote_hashes, "source_unit_quoted_not_authoritative")
    return {
        "source_ref": SOURCE,
        "capture_sha256": receipt,
        "capture_observed_at": captured_at,
        "selected_unit_sha256": unit_hash,
        # Strictly internal, NEVER returned from public audit.
        "_observed_unit": chosen,
    }


def evaluate_live_observed_nli(
    *,
    reader: AllowlistedHttpsSourceReader,
    model: object,
    now: datetime | None = None,
) -> dict[str, Any]:
    """Run 3 real (or test-injected) inferences from exactly one source capture."""
    _require(type(reader) is AllowlistedHttpsSourceReader
             and reader._allowed == frozenset({SOURCE}),
             "unapproved_source_reader")
    _require(callable(getattr(model, "predict", None)), "model_unavailable")
    try:
        observation = reader(SOURCE)  # ONLY ONE network read, pinned URL
    except Exception:
        raise ObservedNLIError("original_source_capture_unavailable") from None
    attestation = select_standalone_observed_unit(observation, now=now)
    premise = attestation.pop("_observed_unit")
    rows = []
    for scenario, hypothesis in CLAIMS:
        _require(0 < len(hypothesis) <= 500 and "\n" not in hypothesis,
                 "invalid_fixed_hypothesis")
        try:
            prediction = model.predict(premise, hypothesis)
        except Exception:
            raise ObservedNLIError("neural_inference_unavailable") from None
        _require(type(prediction) is dict
                 and prediction.get("predicted_relation") in EXPECTED_LABELS
                 and prediction.get("not_a_truth_probability") is True
                 and prediction.get("not_authorized_to_support_claim") is True,
                 "neural_output_not_research_only")
        scores = prediction.get("uncalibrated_model_scores")
        _require(type(scores) is dict
                 and set(scores) == set(EXPECTED_LABELS)
                 and all(type(scores[label]) in (int, float)
                         and math.isfinite(scores[label])
                         and 0 <= scores[label] <= 1 for label in EXPECTED_LABELS)
                 and abs(sum(scores.values()) - 1.0) <= .00001,
                 "neural_output_scores_invalid")
        relationship = _relationship(_parse_atomic(hypothesis), _parse_atomic(premise))
        rows.append({
            "scenario_id": scenario,
            "neural_shadow_prediction": prediction["predicted_relation"],
            "deterministic_text_relation": relationship,
            "neural_may_promote_reality_state": False,
        })
    return {
        "milestone": "step238_live_original_source_neural_nli",
        "source_ref": attestation["source_ref"],
        "capture_sha256": attestation["capture_sha256"],
        "capture_observed_at": attestation["capture_observed_at"],
        "selected_source_unit_sha256": attestation["selected_unit_sha256"],
        "source_captures": 1,
        "reviewed_original_source_unit_count": 1,
        "fixed_developer_claims_evaluated": len(rows),
        "model_repository": MODEL_REPO,
        "model_revision": MODEL_REVISION,
        "onnx_weights_sha256": ONNX_SHA256,
        "neural_model_inference_executed": True,
        "independent_https_source_observed": True,
        "source_publisher_authorship_cryptographically_verified": False,
        "source_website_statement_is_factually_true": None,
        "model_semantic_accuracy_established": False,
        "independent_human_labels": False,
        "uncalibrated_scores_are_truth_probabilities": False,
        "neural_can_authorize_production_claim_support": False,
        "production_api_modified": False,
        "external_deployment": False,
        "cases": rows,
    }


def run_live(*, cache_dir: Path) -> dict[str, Any]:
    # Model weights are checked by the already proven Step237 code; the
    # source reader is the real pinned HTTPS reader used by the product.
    model = load_reviewed_model(cache_dir=cache_dir, live=True)
    return evaluate_live_observed_nli(
        reader=AllowlistedHttpsSourceReader([SOURCE]), model=model
    )


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--live", action="store_true")
    parser.add_argument("--cache-dir", type=Path, default=Path("/tmp/arl-step238-model-cache"))
    args = parser.parse_args(argv)
    if not args.live:
        parser.error("network and inference are disabled by default; --live required")
    try:
        print(json.dumps(run_live(cache_dir=args.cache_dir), sort_keys=True))
        return 0
    except Exception:
        # External server HTML, secrets, local paths and model exception
        # messages cannot escape CI/audit logs.
        print("Step 238 real original-source neural shadow check failed")
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
