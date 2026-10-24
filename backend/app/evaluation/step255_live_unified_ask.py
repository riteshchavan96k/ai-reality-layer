"""Step255 actual HTTPS source -> unified API with no required LLM.

All 10 predeclared official publisher questions are evaluated, including four
previously unseen release versions/questions (3.10.0 / 3.15.0). Frozen labels
are compared with independent source-extracted developer client receipts.
The single optional real model executes separately and cannot change answers.
"""
from __future__ import annotations
import argparse
import json
import os
import secrets
from pathlib import Path
from time import perf_counter
from unittest.mock import patch

from fastapi.testclient import TestClient

from backend.app.api.evidence_first_ask import EvidenceFirstAskRequest
from backend.app.evaluation.step252_local_generative_model import (
    load_real_proposer, MODEL_REPO, MODEL_REVISION, MODEL_SHA256,
)
from backend.app.integrations.evidence_first_ask_client import (
    ask_with_optional_model,
)
from backend.app.main import app
import backend.app.services.evidence_first_ask_service as ask_service
from backend.app.reality.allowlisted_https_source_reader import AllowlistedHttpsSourceReader
from backend.app.evaluation.step254_live_model_value import load_manifest as load_previous

HELDOUT=Path(__file__).resolve().parents[2]/"evaluation_fixtures"/"step255_heldout_official_qa_v1.json"
INDEPENDENT_HELDOUT={
    ("Python 3.10.0","release_date"):"2021-10-04",
    ("Python 3.10.0","release_type"):"stable",
    ("Python 3.15.0","release_date"):"2026-10-09",
    ("Python 3.15.0","release_type"):"stable",
}

def selected_cases():
    prior=load_previous()
    held=json.loads(HELDOUT.read_text(encoding="utf-8"))
    cases=held.get("cases")
    if (
        held.get("schema_version")!="arl-step255-heldout-official-qa-v1"
        or type(cases) is not list or len(cases)!=4
        or len({x["id"] for x in cases})!=4
        or {(x["entity"],x["fact_kind"]):x["expected_value"] for x in cases}
        != INDEPENDENT_HELDOUT
        or len({(x["entity"],x["fact_kind"]) for x in cases})!=4
    ):
        raise ValueError("heldout_manifest_mismatch")
    for x in cases:
        name=x["entity"]
        expected="https://www.python.org/downloads/release/python-"+name[7:].replace(".","")+"/"
        q=(f"When was {name} released?" if x["fact_kind"]=="release_date"
           else f"What type of release was {name}?")
        if x["source_uri"]!=expected or x["question"]!=q:
            raise ValueError("heldout_question_or_url_tampered")
    return prior+cases

def run_live(cache_dir: Path) -> dict:
    cases=selected_cases()
    token=secrets.token_urlsafe(48)
    allowed_urls=sorted({x["source_uri"] for x in cases})
    original=AllowlistedHttpsSourceReader.__call__
    source_reasons=[]
    def date_observe(req):
        observed=orig_date(req)
        source_reasons.append(observed.reason_code)
        return observed
    def status_observe(req):
        observed=orig_status(req)
        source_reasons.append(observed.reason_code)
        return observed
    orig_date=ask_service.observe_release_date
    orig_status=ask_service.observe_release_status
    reads=[]
    def count_read(self,uri):
        reads.append(uri)
        return original(self,uri)
    config={
        "ARL_RUNTIME_MODE":"pilot",
        "ARL_PILOT_BEARER_TOKEN":token,
        "ARL_INDEPENDENT_SOURCE_ALLOWED_URLS":json.dumps(allowed_urls),
    }
    correct=0
    heldout_correct=0
    false_support=0
    abstain=0
    warm_latency_ms=[]
    observed_without_model=0
    case_receipts=[]
    with patch.dict(os.environ,config),patch.object(
        AllowlistedHttpsSourceReader,"__call__",count_read
    ),patch.object(ask_service,"observe_release_date",date_observe),patch.object(
        ask_service,"observe_release_status",status_observe
    ):
        with TestClient(app) as client:
            for x in cases:
                req=EvidenceFirstAskRequest(question=x["question"],entity=x["entity"])
                before=len(reads)
                start=perf_counter()
                result=ask_with_optional_model(client,token,req)
                warm_latency_ms.append(round((perf_counter()-start)*1000,2))
                if len(reads)!=before+1 or reads[-1]!=x["source_uri"]:
                    raise ValueError("unified_one_source_capture_contract_broken")
                if result.optional_model_assessment!="not_requested":
                    raise ValueError("model_was_required_for_direct_answer")
                observed_without_model+=1
                if result.outcome=="bounded_source_answer":
                    if not (
                        result.answer_value==x["expected_value"]
                        and result.citation is not None
                        and result.citation.source_uri==x["source_uri"]
                        and result.may_use_as_bounded_evidence
                        and not result.factual_truth_verified
                        and not result.publisher_authorship_verified
                    ):
                        false_support+=1
                    else:
                        correct+=1
                        if x["id"] in ("py310-date","py310-type","py315-date","py315-type"):
                            heldout_correct+=1
                else:
                    abstain+=1
                # Safe structured diagnostics: predeclared ID, bounded status
                # and reason only; never emit the body, quote, token, or URI.
                case_receipts.append({
                    "id":x["id"],"outcome":result.outcome,
                    "source_reason":source_reasons[-1] if source_reasons else None,
                    "reason":result.reason_code,
                    "matched":(result.outcome=="bounded_source_answer"
                               and result.answer_value==x["expected_value"]),
                })
            if correct!=len(cases) or heldout_correct!=4 or false_support or abstain:
                print("step255_official_case_outcomes="+json.dumps(case_receipts,sort_keys=True))
                raise ValueError("real_heldout_source_answer_quality_failed")

            # Preflight unsupported query and wrong bearer: zero additional
            # original-source network activity, even though source is approved.
            sentinel=len(reads)
            denied=ask_with_optional_model(
                client,token+"invalid",
                EvidenceFirstAskRequest(
                    question="When was Python 3.13.0 released?",entity="Python 3.13.0"
                ),
            )
            invalid=ask_with_optional_model(
                client,token,
                EvidenceFirstAskRequest(
                    question="What is Python 3.13.0's current security status?",
                    entity="Python 3.13.0"
                ),
            )
            if (denied.outcome!="abstain" or invalid.outcome!="abstain"
                or denied.citation is not None or invalid.citation is not None
                or len(reads)!=sentinel):
                raise ValueError("invalid_question_or_bearer_triggered_network")

            model=load_real_proposer(cache_dir=cache_dir,live=True)
            research=EvidenceFirstAskRequest(
                question="What type of release was Python 3.15.0?",
                entity="Python 3.15.0",
            )
            before=len(reads)
            optional=ask_with_optional_model(client,token,research,model=model)
            if (
                optional.outcome!="bounded_source_answer"
                or optional.answer_value!="stable"
                or optional.citation is None
                or optional.optional_model_assessment not in (
                    "model_agrees","model_disagrees"
                )
                or len(reads)!=before+1
            ):
                raise ValueError("optin_real_model_changed_or_blocked_verified_answer")
    return {
        "milestone":"step255_evidence_first_unified_question_api",
        "predeclared_cases":len(cases),
        "previously_unseen_cases":4,
        "heldout_correct":heldout_correct,
        "direct_verified_source_answers":correct,
        "direct_answer_abstentions":abstain,
        "falsely_supported_within_cases":false_support,
        "direct_answers_without_model":observed_without_model,
        "exact_source_https_reads":len(reads),
        "one_exact_source_read_per_supported_request":True,
        "wrong_bearer_and_unsupported_no_reads":True,
        "optional_genuine_pretrained_model_executed":True,
        "optional_model_observation":optional.optional_model_assessment,
        "model_can_override_or_veto_source":False,
        "real_model":MODEL_REPO,
        "real_model_revision":MODEL_REVISION,
        "real_model_weights_sha256":MODEL_SHA256,
        "direct_answer_warm_latency_ms":{
            "min":min(warm_latency_ms),"max":max(warm_latency_ms),
            "mean":round(sum(warm_latency_ms)/len(warm_latency_ms),2),
        },
        "independently_publisher_signed":False,
        "general_world_accuracy_established":False,
        "externally_deployed":False,
        "gpu_provisioned":False,
    }

def main(argv=None) -> int:
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument("--live",action="store_true")
    p.add_argument("--cache-dir",type=Path,
                   default=Path("/tmp/arl-step255-hf-cache"))
    args=p.parse_args(argv)
    if not args.live:
        p.error("official-source/model HTTPS requires explicit --live")
    try:
        print(json.dumps(run_live(args.cache_dir),sort_keys=True))
        return 0
    except Exception as exc:
        # Diagnostics are deliberately location-only: never log credentials,
        # original publisher text, URLs, model outputs or exception messages.
        import traceback
        frames = traceback.extract_tb(exc.__traceback__)
        tail = ",".join(
            f"{Path(frame.filename).name}:{frame.lineno}" for frame in frames[-4:]
        )
        print(f"Step 255 real unified question benchmark failed: {type(exc).__name__} at {tail}")
        return 1

if __name__=="__main__":
    raise SystemExit(main())
