"""Actual original Python.org HTTPS -> new claim-only FastAPI API canary.

Requires --live, uses one fixed operator-reviewed source and no external
hosting or user-driven fetch origins. The endpoint itself uses real DNS,
TLS, bounded original-source text and the complete Reality State pipeline.
This is a policy smoke, not semantic/factual accuracy evaluation.
"""

from __future__ import annotations

import argparse
from hashlib import sha256
import json
import os
import re
import secrets
from unittest.mock import patch

from fastapi.testclient import TestClient

from backend.app.main import app

ORIGINAL = "https://www.python.org/downloads/release/python-3130/"
POSITIVE = "Python 3.13.0 is a stable release."
NEGATIVE = "Python 3.13.0 is not a stable release."


class ClaimOnlyLiveGateError(ValueError):
    """A bounded failure without source HTML, exception text or secrets."""


def run_live() -> dict:
    token = secrets.token_urlsafe(48)
    env = {
        "ARL_RUNTIME_MODE": "pilot",
        "ARL_PILOT_BEARER_TOKEN": token,
        "ARL_INDEPENDENT_SOURCE_ALLOWED_URLS": json.dumps([ORIGINAL]),
    }

    def request(claim: str):
        return {
            "entity": "Python 3.13.0",
            "claim_text": claim,
            "source_uri": ORIGINAL,
            "freshness_max_age_seconds": 3600,
        }

    with patch.dict(os.environ, env):
        with TestClient(app) as client:
            headers = {"Authorization": "Bearer " + token}
            response = client.post(
                "/api/v1/reality-state/claim", json=request(POSITIVE), headers=headers
            )
            if response.status_code != 200:
                raise ClaimOnlyLiveGateError("positive_api_unavailable")
            positive = response.json()
            if (
                positive.get("status") != "supported"
                or positive.get("source_ref") != ORIGINAL
                or not isinstance(positive.get("reality_state"), dict)
            ):
                raise ClaimOnlyLiveGateError("positive_single_capture_abstained")
            alignment = positive["reality_state"].get("evidence", {}).get("claim_alignment", {})
            receipts = positive["reality_state"].get("evidence", {}).get(
                "independent_source_text_assurance", {}
            ).get("sources", [])
            if (
                alignment.get("status") != "aligned"
                or alignment.get("semantic_support_verified") is not False
                or alignment.get("factual_truth_verified") is not False
                or alignment.get("decision_reasons") != [
                    {"source_ref": ORIGINAL, "code": "bounded_assertion_aligned"}
                ]
                or not isinstance(receipts, list) or len(receipts) != 1
                or receipts[0].get("source_ref") != ORIGINAL
                or not isinstance(receipts[0].get("capture_sha256"), str)
                or re.fullmatch(r"[0-9a-f]{64}", receipts[0]["capture_sha256"]) is None
                or not isinstance(receipts[0].get("capture_observed_at"), str)
                or not receipts[0]["capture_observed_at"].endswith("Z")
            ):
                raise ClaimOnlyLiveGateError("positive_capture_or_alignment_not_proven")
            response = client.post(
                "/api/v1/reality-state/claim", json=request(NEGATIVE), headers=headers
            )
            if response.status_code != 200:
                raise ClaimOnlyLiveGateError("negation_api_unavailable")
            negative = response.json()
            if (
                negative.get("status") == "supported"
                or not isinstance(negative.get("reality_state"), dict)
                or negative["reality_state"].get("evidence", {})
                .get("claim_alignment", {}).get("status") != "contradicted"
            ):
                raise ClaimOnlyLiveGateError("negation_not_safely_refused")

    return {
        "evaluation": "original_source_claim_only_reality_state_live_policy_smoke",
        "source_count": 1,
        "actual_original_publisher_https": True,
        "claim_only_api_supported_fixed_positive": True,
        "claim_only_api_refused_fixed_negation": True,
        "semantically_entailed": False,
        "factual_truth_verified": False,
        "general_field_accuracy_established": False,
        "externally_deployed": False,
        # No raw source, credential, response body or secret token printed.
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--live", action="store_true")
    args = parser.parse_args(argv)
    if not args.live:
        parser.error("original-source network disabled by default; --live required")
    try:
        print(json.dumps(run_live(), sort_keys=True))
        return 0
    except Exception:
        # Treat all exceptions as fixed errors, including library transport and
        # source parsing errors; no traces or source bytes enter build logs.
        print("Core original-source claim-only live policy canary failed")
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
