"""Step241: genuine Python.org TLS -> authenticated first source-cited answer API.

Deliberately network-opt-in. Logs only bounded booleans, never original source
quotes, bearer tokens, response bodies, model outputs or untrusted exceptions.
"""

from __future__ import annotations

import argparse
from hashlib import sha256
import json
import os
import secrets
from unittest.mock import patch

from fastapi.testclient import TestClient

from backend.app.api.original_source_claim import OriginalSourceClaimRequest
from backend.app.main import app

SOURCE = "https://www.python.org/downloads/release/python-3130/"


def run_live() -> dict:
    token = secrets.token_urlsafe(48)
    env = {
        "ARL_RUNTIME_MODE": "pilot",
        "ARL_PILOT_BEARER_TOKEN": token,
        "ARL_INDEPENDENT_SOURCE_ALLOWED_URLS": json.dumps([SOURCE]),
    }

    def request(claim, source=SOURCE):
        return OriginalSourceClaimRequest(
            claim_text=claim, entity="Python 3.13.0",
            source_uri=source, freshness_max_age_seconds=3600,
        )

    def send(client, rq, bearer=token):
        return client.post(
            "/api/v1/reality-state/answer",
            json=rq.model_dump(mode="json"),
            headers={"Authorization": "Bearer " + bearer},
        )

    with patch.dict(os.environ, env):
        with TestClient(app) as client:
            supported = send(client, request("Python 3.13.0 is a stable release."))
            contradicted = send(client, request("Python 3.13.0 is not a stable release."))
            unsupported = send(client, request("Python 3.13.0 is production-ready."))
            refused_source = send(
                client, request("Python 3.13.0 is a stable release.",
                                source="https://www.python.org/other-unapproved/")
            )
            refused_auth = send(
                client, request("Python 3.13.0 is a stable release."),
                bearer=token + "bad",
            )

    if not (
        supported.status_code == contradicted.status_code == 200
        and unsupported.status_code == refused_source.status_code == 200
        and refused_auth.status_code in (401, 403)
    ):
        raise ValueError("unexpected_live_authenticated_answer_http_contract")
    s, c, u, f = (
        supported.json(), contradicted.json(),
        unsupported.json(), refused_source.json(),
    )

    def valid_citation(data):
        cite = data.get("citation")
        if not isinstance(cite, dict):
            return False
        quote = cite.get("original_source_quote")
        return (
            cite.get("source_uri") == SOURCE
            and isinstance(quote, str)
            and 0 < len(quote) <= 500
            and sha256(quote.encode()).hexdigest() == cite.get("source_quote_sha256")
            and isinstance(cite.get("source_capture_sha256"), str)
            and len(cite["source_capture_sha256"]) == 64
            and isinstance(cite.get("source_capture_observed_at"), str)
            and cite["source_capture_observed_at"].endswith("Z")
            and data.get("original_source_observed") is True
            and data.get("factual_truth_verified") is False
            and data.get("publisher_authorship_verified") is False
            and data.get("neural_model_used") is False
        )

    if not (
        s.get("outcome") == "bounded_source_support"
        and c.get("outcome") == "bounded_source_contradiction"
        and valid_citation(s) and valid_citation(c)
        and s["citation"]["original_source_quote"]
            == c["citation"]["original_source_quote"]
        and u.get("outcome") == f.get("outcome") == "abstain"
        and u.get("citation") is None and f.get("citation") is None
        and u.get("original_source_observed") is False
        and f.get("original_source_observed") is False
        and all(x.get("factual_truth_verified") is False
                and x.get("general_question_answering") is False
                for x in (s, c, u, f))
    ):
        raise ValueError("real_original_source_cited_answer_contract_failed")
    return {
        "milestone": "step241_live_bounded_source_cited_answer",
        "genuine_original_publisher_https": True,
        "real_authenticated_fastapi_endpoint": True,
        "bounded_positive_source_citation": True,
        "bounded_contradiction_source_citation": True,
        "same_original_source_statement_as_quote": True,
        "sha256_bound_source_excerpt": True,
        "unsupported_claim_abstains_without_citation": True,
        "unapproved_source_abstains_without_citation": True,
        "bad_auth_denied": True,
        "factual_truth_verified": False,
        "publisher_authorship_verified": False,
        "neural_model_executed": False,
        "general_question_answering": False,
        "externally_deployed": False,
    }


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--live", action="store_true")
    args = parser.parse_args(argv)
    if not args.live:
        parser.error("real network disabled by default; --live explicitly required")
    try:
        print(json.dumps(run_live(), sort_keys=True))
        return 0
    except Exception:
        print("Step 241 bounded source-cited answer canary failed")
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
