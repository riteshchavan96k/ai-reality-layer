"""Step242 real publisher HTTPS -> authenticated FastAPI -> app-client acceptance.

Opt-in network only. Prints safe booleans, never original publisher text,
Authorization credentials, responses, untrusted errors or quote digests.
"""

from __future__ import annotations

import argparse
import json
import os
import secrets
from unittest.mock import patch

from fastapi.testclient import TestClient

from backend.app.api.original_source_claim import OriginalSourceClaimRequest
from backend.app.integrations.cited_answer_client import check_cited_answer_with_api
from backend.app.main import app

SOURCE = "https://www.python.org/downloads/release/python-3130/"


def run_live() -> dict:
    token = secrets.token_urlsafe(48)
    configured = {
        "ARL_RUNTIME_MODE": "pilot",
        "ARL_PILOT_BEARER_TOKEN": token,
        "ARL_INDEPENDENT_SOURCE_ALLOWED_URLS": json.dumps([SOURCE]),
    }

    def request(text: str, source=SOURCE):
        return OriginalSourceClaimRequest(
            claim_text=text,
            entity="Python 3.13.0",
            source_uri=source,
            freshness_max_age_seconds=3600,
        )

    with patch.dict(os.environ, configured):
        with TestClient(app) as client:
            supported = check_cited_answer_with_api(
                client, token, request("Python 3.13.0 is a stable release.")
            )
            contradicted = check_cited_answer_with_api(
                client, token, request("Python 3.13.0 is not a stable release.")
            )
            unsupported = check_cited_answer_with_api(
                client, token, request("Python 3.13.0 is production-ready.")
            )
            denied_source = check_cited_answer_with_api(
                client, token, request(
                    "Python 3.13.0 is a stable release.",
                    source="https://www.iana.org/domains/reserved",
                ),
            )
            denied_auth = check_cited_answer_with_api(
                client, token + "bad", request("Python 3.13.0 is a stable release.")
            )

    if not (
        supported.decision == "bounded_source_support"
        and contradicted.decision == "bounded_source_contradiction"
        and supported.may_use_as_bounded_evidence is True
        and contradicted.may_use_as_bounded_evidence is False
        and supported.citation is not None
        and contradicted.citation is not None
        and supported.citation.source_uri == SOURCE
        and contradicted.citation.source_uri == SOURCE
        and supported.citation.original_source_quote
            == contradicted.citation.original_source_quote
        and supported.citation.source_capture_observed_at.endswith("Z")
        and unsupported.decision == "abstain" and unsupported.citation is None
        and denied_source.decision == "abstain" and denied_source.citation is None
        and denied_auth.decision == "abstain" and denied_auth.citation is None
        and denied_auth.reason_code == "api_unavailable_or_invalid"
        and all(
            v.factual_truth_verified is False
            and v.publisher_authorship_verified is False
            and v.neural_model_used is False
            and v.general_question_answering is False
            for v in (supported, contradicted, unsupported, denied_source, denied_auth)
        )
    ):
        raise ValueError("bounded_cited_client_live_acceptance_failed")
    return {
        "milestone": "step242_real_original_source_to_ai_application_client",
        "real_publisher_https": True,
        "authenticated_local_fastapi": True,
        "client_source_citation_consistent": True,
        "client_source_contradiction_not_promoted": True,
        "unsupported_claim_abstains": True,
        "unapproved_source_abstains": True,
        "bad_auth_abstains": True,
        "factual_truth_verified": False,
        "publisher_authorship_verified": False,
        "general_question_answering": False,
        "externally_deployed": False,
    }


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--live", action="store_true")
    args = parser.parse_args(argv)
    if not args.live:
        parser.error("live source network disabled unless --live is provided")
    try:
        print(json.dumps(run_live(), sort_keys=True))
        return 0
    except Exception:
        print("Step 242 real cited-answer application client canary failed")
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
