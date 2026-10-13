"""Step 235: genuine original publisher HTTPS -> actual AI consumer decision gate.

Run with --live only. All URLs/claims are fixed and operator-reviewed; each
API call fetches real original Python.org over pinned TLS. Logs only policy
outcomes, never token, raw source text, response body or network exceptions.
"""

from __future__ import annotations

import argparse
import json
import os
import secrets
from unittest.mock import patch

from fastapi.testclient import TestClient

from backend.app.api.original_source_claim import OriginalSourceClaimRequest
from backend.app.integrations.ai_claim_gate import check_claim_with_api
from backend.app.main import app

SOURCE = "https://www.python.org/downloads/release/python-3130/"


def run_live() -> dict:
    token = secrets.token_urlsafe(48)
    env = {
        "ARL_RUNTIME_MODE": "pilot",
        "ARL_PILOT_BEARER_TOKEN": token,
        "ARL_INDEPENDENT_SOURCE_ALLOWED_URLS": json.dumps([SOURCE]),
    }

    def request(text):
        return OriginalSourceClaimRequest(
            entity="Python 3.13.0",
            claim_text=text,
            source_uri=SOURCE,
            freshness_max_age_seconds=3600,
        )

    with patch.dict(os.environ, env):
        with TestClient(app) as client:
            positive = check_claim_with_api(
                client, token, request("Python 3.13.0 is a stable release.")
            )
            negative = check_claim_with_api(
                client, token, request("Python 3.13.0 is not a stable release.")
            )
            unapproved = check_claim_with_api(
                client, token,
                OriginalSourceClaimRequest(
                    entity="Python 3.13.0",
                    claim_text="Python 3.13.0 is a stable release.",
                    source_uri="https://www.python.org/unreviewed-step235/",
                ),
            )
            denied = check_claim_with_api(
                client, token + "-wrong",
                request("Python 3.13.0 is a stable release."),
            )

    if not (
        positive.decision == "bounded_supported"
        and positive.may_use_as_bounded_evidence is True
        and positive.source_ref == SOURCE
        and positive.semantic_truth_verified is False
        and positive.publisher_authorship_verified is False
        and negative.decision == "bounded_contradicted"
        and negative.may_use_as_bounded_evidence is False
        and unapproved.decision == "abstain"
        and denied.decision == "abstain"
    ):
        raise ValueError("bounded_source_consumer_policy_failed")
    return {
        "audit": "step235_original_publisher_ai_client_integration",
        "independent_real_original_source_https": True,
        "real_authenticated_fastapi": True,
        "bounded_positive_consumed": True,
        "bounded_negation_refused": True,
        "off_allowlist_abstained": True,
        "invalid_auth_abstained": True,
        "general_semantic_truth_verified": False,
        "publisher_authorship_verified": False,
        "externally_deployed": False,
        "independent_human_labeled_accuracy": False,
    }


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--live", action="store_true")
    args = parser.parse_args(argv)
    if not args.live:
        parser.error("network disabled by default; --live explicitly required")
    try:
        print(json.dumps(run_live(), sort_keys=True))
        return 0
    except Exception:
        print("Step 235 bounded AI consumer original-source canary failed")
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
