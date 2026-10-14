"""Step244 genuine two HTTPS publishers -> authenticated API -> defensive app client.

Opt-in real network only. The second source is intentionally irrelevant so the
verified result MUST abstain. No positive dual-publisher claim is made.
Never print source text, URLs with secrets, quote digests or bearer credentials.
"""
from __future__ import annotations

import argparse
import json
import os
import secrets
from unittest.mock import patch

from fastapi.testclient import TestClient

from backend.app.api.two_origin_answer import TwoOriginAnswerRequest
from backend.app.integrations.two_origin_answer_client import (
    check_two_origin_answer_with_api,
)
from backend.app.main import app
from backend.app.reality.allowlisted_https_source_reader import AllowlistedHttpsSourceReader

PYTHON = "https://www.python.org/downloads/release/python-3130/"
IANA = "https://www.iana.org/domains/reserved"
OFF_LIST = "https://go.dev/dl/"

def _request(urls):
    return TwoOriginAnswerRequest(
        claim_text="Python 3.13.0 is a stable release.",
        entity="Python 3.13.0",
        source_uris=urls,
        freshness_max_age_seconds=3600,
    )

def run_live() -> dict:
    token = secrets.token_urlsafe(48)
    environment = {
        "ARL_RUNTIME_MODE": "pilot",
        "ARL_PILOT_BEARER_TOKEN": token,
        "ARL_INDEPENDENT_SOURCE_ALLOWED_URLS": json.dumps([PYTHON, IANA]),
    }
    original = AllowlistedHttpsSourceReader.__call__
    reads = []

    def instrumented_reader(self, url):
        reads.append(url)
        return original(self, url)

    with patch.dict(os.environ, environment), patch.object(
        AllowlistedHttpsSourceReader, "__call__", instrumented_reader
    ):
        with TestClient(app) as client:
            original_order = check_two_origin_answer_with_api(
                client, token, _request([PYTHON, IANA])
            )
            after_original = list(reads)
            reversed_order = check_two_origin_answer_with_api(
                client, token, _request([IANA, PYTHON])
            )
            after_reversed = list(reads)
            denied_auth = check_two_origin_answer_with_api(
                client, token + "bad", _request([PYTHON, IANA])
            )
            denied_origin = check_two_origin_answer_with_api(
                client, token, _request([PYTHON, OFF_LIST])
            )
    checked = (original_order, reversed_order, denied_auth, denied_origin)
    if not (
        all(
            entry.decision == "abstain"
            and entry.citations == ()
            and entry.may_use_as_bounded_evidence is False
            and entry.factual_truth_verified is False
            and entry.publisher_authorship_verified is False
            and entry.independently_owned_publishers_verified is False
            and entry.neural_model_used is False
            and entry.general_question_answering is False
            for entry in checked
        )
        and original_order.reason_code == "source_abstained"
        and reversed_order.reason_code == "source_abstained"
        and denied_auth.reason_code == "api_unavailable_or_invalid"
        and denied_origin.reason_code == "source_abstained"
        and after_original == [PYTHON, IANA]
        and after_reversed == [PYTHON, IANA, IANA]
        and reads == after_reversed
    ):
        raise ValueError("Step244 dual-host app consumer contract failed")
    return {
        "milestone": "step244_real_https_to_two_source_app_client",
        "real_python_and_iana_https_captures": True,
        "authenticated_local_fastapi": True,
        "application_client_failed_closed_for_irrelevant_source": True,
        "both_source_orders_conservative": True,
        "no_partial_source_receipts_exposed": True,
        "invalid_auth_and_offlist_failed_without_network_fetch": True,
        "real_dual_source_positive_corroboration_demonstrated": False,
        "publisher_independence_proven": False,
        "factual_truth_verified": False,
        "externally_deployed": False,
    }

def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--live", action="store_true")
    options = parser.parse_args(argv)
    if not options.live:
        parser.error("network canary requires explicit --live")
    try:
        print(json.dumps(run_live(), sort_keys=True))
        return 0
    except Exception:
        print("Step244 real source-to-client canary failed")
        return 1

if __name__ == "__main__":
    raise SystemExit(main())
