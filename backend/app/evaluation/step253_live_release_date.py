"""Step253 genuine FLAN-T5 answer extraction from independently captured Python.org."""
from __future__ import annotations

import argparse
import json
import os
from pathlib import Path
import secrets
from unittest.mock import patch
from fastapi.testclient import TestClient

from backend.app.api.release_date import ReleaseDateSourceRequest
from backend.app.evaluation.step252_local_generative_model import (
    load_real_proposer, MODEL_REPO, MODEL_REVISION, MODEL_SHA256,
)
from backend.app.integrations.release_date_answer_client import (
    check_release_date_with_model,
)
from backend.app.main import app
from backend.app.reality.allowlisted_https_source_reader import AllowlistedHttpsSourceReader

SOURCE="https://www.python.org/downloads/release/python-3130/"
QUESTION="When was Python 3.13.0 released?"


def run_live(cache_dir: Path) -> dict:
    model=load_real_proposer(cache_dir=cache_dir,live=True)
    token=secrets.token_urlsafe(48)
    config={
        "ARL_RUNTIME_MODE":"pilot",
        "ARL_PILOT_BEARER_TOKEN":token,
        "ARL_INDEPENDENT_SOURCE_ALLOWED_URLS":json.dumps([SOURCE]),
    }
    original=AllowlistedHttpsSourceReader.__call__
    count={"reads":0}
    def read_actual(self,uri):
        count["reads"]+=1
        return original(self,uri)
    request=ReleaseDateSourceRequest(
        question=QUESTION,entity="Python 3.13.0",source_uri=SOURCE,
        freshness_max_age_seconds=3600.0,
    )
    with patch.dict(os.environ,config), patch.object(
        AllowlistedHttpsSourceReader,"__call__",read_actual
    ):
        with TestClient(app) as client:
            output=check_release_date_with_model(client,token,request,model)
            if not (
                output.outcome=="bounded_source_date"
                and output.answer_iso=="2024-10-07"
                and output.citation is not None
                and output.citation.source_uri==SOURCE
                and output.citation.source_capture_observed_at.endswith("Z")
                and output.citation.original_source_quote
                    .casefold().startswith("release date:")
                and output.may_use_as_bounded_evidence
                and output.model_executed
                and count["reads"]==1
                and not output.factual_truth_verified
                and not output.publisher_authorship_verified
            ):
                raise ValueError("genuine_release_date_model_source_gate_refused")
            denied=check_release_date_with_model(
                client,token+"invalid",request,model
            )
            invalid=check_release_date_with_model(
                client,token,request.model_copy(update={
                    "question":"What is the date of every Python release?"
                }),model
            )
            offsite=check_release_date_with_model(
                client,token,request.model_copy(update={
                    "source_uri":"https://www.iana.org/domains/reserved"
                }),model
            )
            if not (
                denied.outcome==invalid.outcome==offsite.outcome=="abstain"
                and denied.citation is None
                and invalid.citation is None
                and offsite.citation is None
                and count["reads"]==1
            ):
                raise ValueError("genuine_release_date_auth_or_scope_failed")
    return {
        "milestone":"step253_real_evidence_conditioned_release_date",
        "real_pretrained_generative_model_executed":True,
        "model_repository":MODEL_REPO,
        "model_revision":MODEL_REVISION,
        "model_weights_sha256":MODEL_SHA256,
        "original_source_https_captures":count["reads"],
        "one_capture_freshness_and_quote_receipt":True,
        "unknown_date_extracted_from_captured_source":True,
        "generated_date_exactly_checked_against_original_source":True,
        "authenticated_application_api":True,
        "wrong_bearer_and_scope_abstained_without_egress":True,
        "source_authorship_verified":False,
        "general_question_answering":False,
        "world_factual_truth_verified":False,
        "externally_deployed":False,
    }


def main(argv=None):
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--live",action="store_true")
    parser.add_argument("--cache-dir",type=Path,
                        default=Path("/tmp/arl-step253-hf-cache"))
    args=parser.parse_args(argv)
    if not args.live:
        parser.error("real model and source HTTPS require explicit --live")
    try:
        print(json.dumps(run_live(args.cache_dir),sort_keys=True))
        return 0
    except Exception:
        print("Step 253 real evidence-conditioned release-date check failed")
        return 1


if __name__=="__main__":
    raise SystemExit(main())
