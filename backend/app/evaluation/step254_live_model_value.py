"""Step254: frozen real-official-source multi-case model-value study.

This study includes three official Python.org release versions and two facts
per version. It does not establish population factual accuracy, publisher
authorship or general question answering. Real model only after strict
original-source receipt. Emits metrics, no raw source/model/credential data.
"""
from __future__ import annotations
import argparse
import json
import os
import secrets
from collections import Counter
from pathlib import Path
from time import perf_counter
from unittest.mock import patch

from fastapi.testclient import TestClient
from backend.app.main import app
from backend.app.api.release_date import ReleaseDateSourceRequest
from backend.app.api.release_status import ReleaseStatusSourceRequest
from backend.app.evaluation.step252_local_generative_model import (
    load_real_proposer,MODEL_REPO,MODEL_REVISION,MODEL_SHA256,
)
from backend.app.integrations.release_date_answer_client import (
    check_release_date_with_model, _verified_receipt as valid_date_receipt,
)
from backend.app.integrations.release_status_answer_client import (
    check_release_status_with_model, validate_status_receipt,
)
from backend.app.reality.allowlisted_https_source_reader import AllowlistedHttpsSourceReader
from backend.app.reality.release_date_policy import parse_release_date_label
from backend.app.reality.release_status_policy import (
    select_release_type_unit
)

FIXTURE=Path(__file__).resolve().parents[2]/"evaluation_fixtures"/"step254_real_official_answer_v1.json"
EXPECTED_GOLD={
    ("Python 3.11.0","release_date"):"2022-10-24",
    ("Python 3.11.0","release_type"):"stable",
    ("Python 3.12.0","release_date"):"2023-10-02",
    ("Python 3.12.0","release_type"):"stable",
    ("Python 3.13.0","release_date"):"2024-10-07",
    ("Python 3.13.0","release_type"):"stable",
}
def load_manifest():
    manifest=json.loads(FIXTURE.read_text(encoding="utf-8"))
    cases=manifest.get("cases")
    if (manifest.get("schema_version")!="arl-step254-source-coverage-v1"
        or type(cases) is not list or len(cases)!=6
        or len({x["id"] for x in cases})!=6
        or {(x["entity"],x["fact_kind"]):x["expected_value"] for x in cases}!=EXPECTED_GOLD
        or len({(x["entity"],x["fact_kind"]) for x in cases})!=6
    ):
        raise ValueError("official_case_manifest_changed")
    for row in cases:
        name=row["entity"]
        url="https://www.python.org/downloads/release/python-"+name[7:].replace(".","")+"/"
        kind=row["fact_kind"]
        question=(f"When was {name} released?" if kind=="release_date"
                  else f"What type of release was {name}?")
        if row["source_uri"]!=url or row["question"]!=question:
            raise ValueError("official_case_request_binding_changed")
    return cases

def run_live(cache_dir: Path) -> dict:
    cases=load_manifest()
    model=load_real_proposer(cache_dir=cache_dir,live=True)
    token=secrets.token_urlsafe(48)
    urls=sorted({x["source_uri"] for x in cases})
    original=AllowlistedHttpsSourceReader.__call__
    reads={"count":0}
    def read(self,uri):
        reads["count"]+=1
        return original(self,uri)
    config={
        "ARL_RUNTIME_MODE":"pilot",
        "ARL_PILOT_BEARER_TOKEN":token,
        "ARL_INDEPENDENT_SOURCE_ALLOWED_URLS":json.dumps(urls),
    }
    baseline_correct=0
    generated_correct=0
    generated_false_support=0
    generated_abstain=0
    status_generated_correct=0
    per_type=Counter()
    latency_ms=[]
    class RecordingTransport:
        """Record the ONE actual authenticated API response before LLM abstention."""
        def __init__(self,real):
            self.real=real
            self.response=None
        def post(self,*args,**kwargs):
            result=self.real.post(*args,**kwargs)
            self.response=result.json() if result.status_code==200 else None
            return result

    with patch.dict(os.environ,config),patch.object(
        AllowlistedHttpsSourceReader,"__call__",read
    ):
        with TestClient(app) as client:
            recorder=RecordingTransport(client)
            for row in cases:
                recorder.response=None
                first=perf_counter()
                if row["fact_kind"]=="release_date":
                    req=ReleaseDateSourceRequest(
                        question=row["question"],entity=row["entity"],
                        source_uri=row["source_uri"]
                    )
                    output=check_release_date_with_model(recorder,token,req,model)
                    direct=valid_date_receipt(recorder.response,req)
                    if direct is None:
                        accepted=None
                    else:
                        source_date=parse_release_date_label(
                            direct[0].original_source_quote
                        )
                        accepted=source_date.isoformat() if source_date else None
                    actual=output.answer_iso
                    used=output.model_executed
                    allowed=output.outcome=="bounded_source_date"
                else:
                    req=ReleaseStatusSourceRequest(
                        question=row["question"],entity=row["entity"],
                        source_uri=row["source_uri"]
                    )
                    output=check_release_status_with_model(recorder,token,req,model)
                    direct=validate_status_receipt(recorder.response,req)
                    accepted=("stable" if direct is not None
                              and select_release_type_unit(
                                  row["entity"]+"\n"+direct.original_source_quote,
                                  row["entity"]
                              )==direct.original_source_quote else None)
                    actual=output.answer_type
                    used=output.model_executed
                    allowed=output.outcome=="bounded_source_release_type"
                latency_ms.append(round((perf_counter()-first)*1000,2))
                if accepted==row["expected_value"]:
                    baseline_correct+=1
                else:
                    # Independently selected source failed / changed, never
                    # quietly exclude its denominator from the benchmark.
                    raise ValueError("predeclared_official_source_case_unverified")
                if not used:
                    raise ValueError("model_not_executed_for_predeclared_case")
                if allowed:
                    if (actual!=row["expected_value"] or actual!=accepted
                        or not output.may_use_as_bounded_evidence):
                        generated_false_support+=1
                    else:
                        generated_correct+=1
                        per_type[row["fact_kind"]]+=1
                        if row["fact_kind"]=="release_type":
                            status_generated_correct+=1
                else:
                    if actual is not None or output.citation is not None:
                        raise ValueError("model_abstention_leaked_source")
                    generated_abstain+=1
            if reads["count"]!=len(cases):
                raise ValueError("original_source_capture_count_wrong")
    if generated_false_support or generated_correct+generated_abstain!=len(cases):
        raise ValueError("neural_false_source_support_detected")
    # If no real-model release-type output succeeds, there is no evidence
    # of the new model-backed feature and this milestone must NOT pass.
    if status_generated_correct<1:
        raise ValueError("genuine_release_type_model_coverage_not_demonstrated")
    return {
        "milestone":"step254_real_source_model_value_evaluation",
        "case_count":len(cases),
        "distinct_versions":len(urls),
        "supported_fact_types":["release_date","release_type"],
        "real_python_org_original_source_https_observations":reads["count"],
        "deterministic_baseline_correct":baseline_correct,
        "model_supported_correct":generated_correct,
        "model_abstained":generated_abstain,
        "model_false_supported":generated_false_support,
        "model_release_type_correct":status_generated_correct,
        "net_model_coverage_gain_over_deterministic":generated_correct-baseline_correct,
        "model_success_by_fact_type":dict(per_type),
        "end_to_end_latency_ms":{"min":min(latency_ms),"max":max(latency_ms),
                                 "mean":round(sum(latency_ms)/len(latency_ms),2)},
        "real_pretrained_neural_inference":True,
        "model":MODEL_REPO,
        "model_revision":MODEL_REVISION,
        "verified_safetensors_sha256":MODEL_SHA256,
        "predeclared_human_reviewed_official_page_labels":True,
        "external_labeler_independence_proven":False,
        "general_factual_accuracy_established":False,
        "publisher_authorship_verified":False,
        "externally_deployed":False,
        "gpu_provisioned":False,
    }

def main(argv=None):
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument("--live",action="store_true")
    p.add_argument("--cache-dir",type=Path,default=Path("/tmp/arl-step254-hf-cache"))
    opts=p.parse_args(argv)
    if not opts.live:
        p.error("real official-source and real-model benchmark requires --live")
    try:
        print(json.dumps(run_live(opts.cache_dir),sort_keys=True))
        return 0
    except Exception:
        print("Step 254 real official-source model-value evaluation failed")
        return 1
if __name__=="__main__":
    raise SystemExit(main())
