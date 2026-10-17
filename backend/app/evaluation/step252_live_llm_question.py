"""Step252 genuine pinned FLAN-T5 CPU -> bounded question -> Python.org HTTPS -> API.

Real model and real original publisher HTTPS; results are bounded source
observations, not world-truth certification or generalized natural-language QA.
No secrets, raw publisher content or untrusted model output is logged.
"""
from __future__ import annotations

import argparse
import json
import os
from pathlib import Path
import secrets
from unittest.mock import patch

from fastapi.testclient import TestClient

from backend.app.evaluation.step252_local_generative_model import (
    load_real_proposer, MODEL_REPO, MODEL_REVISION, MODEL_SHA256,
)
from backend.app.integrations.grounded_question_llm import (
    check_question_with_grounded_llm, _expected_atomic_question,
)
from backend.app.main import app
from backend.app.reality.allowlisted_https_source_reader import AllowlistedHttpsSourceReader

SOURCE = "https://www.python.org/downloads/release/python-3130/"
QUESTION = "Is Python 3.13.0 a stable release?"
ENTITY = "Python 3.13.0"


def run_live(cache_dir: Path) -> dict:
    model = load_real_proposer(cache_dir=cache_dir, live=True)
    bearer = secrets.token_urlsafe(48)
    config = {
        "ARL_RUNTIME_MODE": "pilot",
        "ARL_PILOT_BEARER_TOKEN": bearer,
        "ARL_INDEPENDENT_SOURCE_ALLOWED_URLS": json.dumps([SOURCE]),
    }
    original = AllowlistedHttpsSourceReader.__call__
    count = {"reads": 0}

    def count_real_https(self, uri):
        count["reads"] += 1
        return original(self, uri)

    # Limit the genuine-source canary to ONE publisher capture.
    with patch.dict(os.environ, config), patch.object(
        AllowlistedHttpsSourceReader, "__call__", count_real_https
    ):
        with TestClient(app) as client:
            answer = check_question_with_grounded_llm(
                client, bearer, QUESTION,
                entity=ENTITY, source_uri=SOURCE, model=model,
            )
            if (
                answer.outcome != "bounded_source_support"
                or answer.claim_text is None or answer.citation is None
                or not answer.llm_generated_candidate
                or not answer.may_use_as_bounded_evidence
                or count["reads"] != 1
            ):
                raise ValueError("real_llm_proposal_not_independently_source_supported")
            denied = check_question_with_grounded_llm(
                client, bearer + "wrong", QUESTION,
                entity=ENTITY, source_uri=SOURCE, model=model,
            )
            unapproved = check_question_with_grounded_llm(
                client, bearer, QUESTION,
                entity=ENTITY, source_uri="https://www.iana.org/domains/reserved",
                model=model,
            )
            unsupported = check_question_with_grounded_llm(
                client, bearer, "What is the current real-world state?",
                entity=ENTITY, source_uri=SOURCE, model=model,
            )
            if (
                denied.outcome != "abstain"
                or unapproved.outcome != "abstain"
                or unsupported.outcome != "abstain"
                or denied.citation is not None
                or unapproved.citation is not None
                or unsupported.citation is not None
                or count["reads"] != 1
            ):
                raise ValueError("real_llm_gate_failed_closed")
    return {
        "milestone": "step252_real_question_to_cited_source",
        "real_pretrained_generative_model_executed": True,
        "model_repository": MODEL_REPO,
        "model_revision": MODEL_REVISION,
        "verified_safetensors_sha256": MODEL_SHA256,
        "real_python_org_https_observations": count["reads"],
        "authenticated_cited_answer_api": True,
        "llm_generated_claim_independently_source_verified": True,
        "unapproved_source_and_wrong_auth_denied": True,
        "unsupported_question_abstained": True,
        "model_cannot_upgrade_unsupported_source": True,
        "model_output_never_becomes_a_trust_assertion": True,
        "factual_truth_verified": False,
        "publisher_authorship_verified": False,
        "general_question_answering": False,
        "externally_deployed": False,
    }


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--live", action="store_true")
    parser.add_argument(
        "--cache-dir", type=Path, default=Path("/tmp/arl-step252-llm-cache")
    )
    opts = parser.parse_args(argv)
    if not opts.live:
        parser.error("genuine model download/source HTTPS requires explicit --live")
    try:
        print(json.dumps(run_live(opts.cache_dir), sort_keys=True))
        return 0
    except Exception:
        print("Step 252 real LLM original-source verification failed")
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
