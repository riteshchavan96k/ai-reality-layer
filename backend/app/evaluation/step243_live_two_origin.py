"""Actual Python.org and IANA HTTPS -> authenticated two-host answer rejection canary.

The IANA site is deliberately unrelated to the Python release: safe abstention
is a genuine observed result, NOT real-world two-publisher corroboration.
"""
from __future__ import annotations

import argparse
import json
import os
import secrets
from unittest.mock import patch

from fastapi.testclient import TestClient

from backend.app.api.original_source_claim import OriginalSourceClaimRequest
from backend.app.api.two_origin_answer import TwoOriginAnswerRequest
from backend.app.integrations.cited_answer_client import check_cited_answer_with_api
from backend.app.main import app
from backend.app.reality.allowlisted_https_source_reader import AllowlistedHttpsSourceReader

PYTHON = "https://www.python.org/downloads/release/python-3130/"
IANA = "https://www.iana.org/domains/reserved"
UNAPPROVED = "https://go.dev/dl/"
PATH = "/api/v1/reality-state/answer/compare"

def run_live() -> dict:
    token = secrets.token_urlsafe(48)
    allowed = json.dumps([PYTHON, IANA])
    original = AllowlistedHttpsSourceReader.__call__
    visited: list[str] = []

    def observed(self, uri):
        visited.append(uri)
        return original(self, uri)

    pair = TwoOriginAnswerRequest(
        claim_text="Python 3.13.0 is a stable release.",
        entity="Python 3.13.0",
        source_uris=[PYTHON, IANA],
    )
    single = OriginalSourceClaimRequest(
        claim_text=pair.claim_text, entity=pair.entity, source_uri=PYTHON
    )
    env = {
        "ARL_RUNTIME_MODE": "pilot", "ARL_PILOT_BEARER_TOKEN": token,
        "ARL_INDEPENDENT_SOURCE_ALLOWED_URLS": allowed,
    }
    with patch.dict(os.environ, env), patch.object(
        AllowlistedHttpsSourceReader, "__call__", observed
    ):
        with TestClient(app) as client:
            positive = check_cited_answer_with_api(client, token, single)
            compare = client.post(
                PATH, json=pair.model_dump(mode="json"),
                headers={"Authorization": "Bearer " + token},
            )
            observed_reads = list(visited)
            denied = client.post(
                PATH, json=pair.model_dump(mode="json"),
                headers={"Authorization": "Bearer " + token + "bad"},
            )
            offlist = client.post(
                PATH,
                json={**pair.model_dump(mode="json"),
                      "source_uris": [PYTHON, UNAPPROVED]},
                headers={"Authorization": "Bearer " + token},
            )
    if compare.status_code != 200 or offlist.status_code != 200:
        raise ValueError("missing two-origin API response")
    result, refused = compare.json(), offlist.json()
    if not (
        positive.decision == "bounded_source_support"
        and positive.citation is not None
        and result["outcome"] == "abstain"
        and result["citations"] == []
        and result["source_observation_count"] == 0
        and result["may_use_as_bounded_evidence"] is False
        and result["factual_truth_verified"] is False
        and result["publisher_authorship_verified"] is False
        and result["independently_owned_publishers_verified"] is False
        and observed_reads == [PYTHON, PYTHON, IANA]
        and visited == observed_reads
        and denied.status_code == 401
        and refused["outcome"] == "abstain"
        and refused["citations"] == []
    ):
        raise ValueError("two-origin source refusal contract failed")
    # No raw text, credential, URL response, exception, or source digest in logs.
    return {
        "milestone": "step243_two_host_actual_source_refusal",
        "actual_two_distinct_hostname_https_observations": True,
        "authenticated_local_fastapi": True,
        "irrelevant_second_host_abstained_without_fabricated_support": True,
        "no_partial_citations": True,
        "unauthorized_and_offlist_blocked_without_fetch": True,
        "real_two_source_positive_corroboration_proven": False,
        "independent_publisher_ownership_proven": False,
        "factual_truth_verified": False,
        "externally_deployed": False,
    }

def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--live", action="store_true")
    args = parser.parse_args(argv)
    if not args.live:
        parser.error("real HTTPS access requires --live")
    try:
        print(json.dumps(run_live(), sort_keys=True))
        return 0
    except Exception:
        print("Step243 real HTTPS two-host comparison canary failed")
        return 1

if __name__ == "__main__":
    raise SystemExit(main())
