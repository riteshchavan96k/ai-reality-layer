"""Step250 adversarial live-to-history API and defensive client tests.

Mocked publisher content only. A separate actual Python.org HTTPS integration
is run in the repository's original-source history CI workflow.
"""
from copy import deepcopy
from datetime import datetime, timedelta, timezone
import json
import os
import sqlite3
from types import SimpleNamespace

import pytest
from fastapi.testclient import TestClient

from backend.tests.test_step247 import (
    environment, SOURCE, OFFLIST, TOKEN, POSITIVE, NEGATIVE, KEY,
)
from backend.tests.test_step248 import baseline, append, show
from backend.app.api.original_source_claim import OriginalSourceClaimRequest
from backend.app.integrations.temporal_recheck_client import (
    RECHECK_PATH, check_temporal_reconciliation_with_api,
    interpret_temporal_reconciliation,
)
from backend.app.main import app


def claim(text="Python 3.13.0 is a stable release.", uri=SOURCE):
    return OriginalSourceClaimRequest(
        claim_text=text, entity="Python 3.13.0", source_uri=uri,
        freshness_max_age_seconds=3600.0,
    )


def payload(root, *, request=None):
    return {"root_record_id": root, "claim": (request or claim()).model_dump(mode="json")}


def setup(environment, monkeypatch, *, n=3):
    monkeypatch.setenv("ARL_TEMPORAL_RECHECK_API_ENABLED", "1")
    root=baseline()
    for _ in range(n-1):
        outcome,_=append(root)
        assert outcome == 0
    return root


def post(root, token=TOKEN, *, data=None):
    with TestClient(app) as http:
        return http.post(
            RECHECK_PATH, json=data or payload(root),
            headers={"Authorization": "Bearer " + token},
        )


def test_genuine_local_pilot_reconciles_three_entry_baseline_one_live_read_no_write(environment, monkeypatch):
    state,path=environment
    root=setup(environment,monkeypatch)
    before=path.read_bytes()
    assert state["calls"]==3
    with TestClient(app) as http:
        checked=check_temporal_reconciliation_with_api(http,TOKEN,claim(),root)
        response=http.post(
            RECHECK_PATH,json=payload(root),
            headers={"Authorization": "Bearer " + TOKEN},
        )
    assert checked.outcome=="bounded_reconciliation"
    assert checked.change_status=="capture_unchanged"
    assert checked.baseline_record_id==show(root)[1]["latest_record_id"]
    assert checked.may_use_current_as_bounded_evidence is True
    assert checked.may_use_historical_as_current_evidence is False
    assert checked.factual_truth_verified is False
    assert response.status_code==200
    assert response.headers["cache-control"]=="no-store"
    assert response.json()["outcome"]=="bounded_reconciliation"
    assert "original_source_quote" not in response.text
    assert POSITIVE not in response.text
    assert TOKEN not in response.text
    assert state["calls"]==5  # one read per authenticated reconciliation, none from show
    assert path.read_bytes()==before


def test_bounded_source_change_and_then_contradiction(environment,monkeypatch):
    state,_=environment
    root=setup(environment,monkeypatch,n=1)
    state["body"]=POSITIVE+"\nPublisher styling metadata"
    result=post(root).json()
    assert result["outcome"]=="bounded_reconciliation"
    assert result["change_status"]=="capture_changed_statement_unchanged"
    state["body"]=NEGATIVE
    result=post(root).json()
    assert result["outcome"]=="bounded_reconciliation"
    assert result["change_status"]=="bounded_statement_changed"
    assert result["current"]["decision"]=="bounded_source_contradiction"
    assert result["may_use_current_as_bounded_evidence"] is False


def test_history_reconciliation_explicitly_off_by_default(environment,monkeypatch):
    state,_=environment
    root=baseline()
    monkeypatch.delenv("ARL_TEMPORAL_RECHECK_API_ENABLED",raising=False)
    result=post(root).json()
    assert result["outcome"]=="abstain"
    assert result["reason"]=="reconciliation_not_enabled"
    assert result["previous"] is None
    assert result["current"] is None
    assert state["calls"]==1


@pytest.mark.parametrize("bad",["", "invalid-bearer-that-should-fail-"*2])
def test_bad_or_missing_bearer_denied_without_egress(environment,monkeypatch,bad):
    state,_=environment
    root=setup(environment,monkeypatch,n=1)
    response=post(root,token=bad)
    assert response.status_code==401
    assert state["calls"]==1


def test_development_cannot_use_opted_in_live_recheck(environment,monkeypatch):
    state,_=environment
    root=setup(environment,monkeypatch,n=1)
    monkeypatch.delenv("ARL_PILOT_BEARER_TOKEN")
    monkeypatch.setenv("ARL_RUNTIME_MODE","development")
    response=post(root)
    assert response.json()["outcome"]=="abstain"
    assert state["calls"]==1


def test_wrong_claim_never_reaches_publisher(environment,monkeypatch):
    state,_=environment
    root=setup(environment,monkeypatch,n=1)
    response=post(root,data=payload(root,request=claim(text=NEGATIVE)))
    assert response.json()["outcome"]=="abstain"
    assert response.json()["previous"] is None
    assert state["calls"]==1


def test_offlist_source_never_reaches_publisher(environment,monkeypatch):
    state,_=environment
    root=setup(environment,monkeypatch,n=1)
    result=post(root,data=payload(root,request=claim(uri=OFFLIST)))
    assert result.json()["outcome"]=="abstain"
    assert state["calls"]==1


@pytest.mark.parametrize("value",["0"*32,"A"*32,"../history","x"])
def test_unknown_or_invalid_history_rejects_without_publisher_egress(environment,monkeypatch,value):
    state,_=environment
    root=setup(environment,monkeypatch,n=1)
    response=post(value)
    if value=="0"*32:
        assert response.status_code==200
        assert response.json()["outcome"]=="abstain"
    else:
        assert response.status_code==422
    assert state["calls"]==1


@pytest.mark.parametrize("defect",["edge_mac","record_mac","delete_child"])
def test_corrupt_history_denied_before_fresh_egress(environment,monkeypatch,defect):
    state,path=environment
    root=setup(environment,monkeypatch)
    with sqlite3.connect(path) as db:
        if defect=="edge_mac":
            db.execute("UPDATE source_timeline_edges SET edge_mac=? WHERE sequence=2",("0"*64,))
        elif defect=="record_mac":
            last=db.execute(
                "SELECT record_id FROM source_timeline_edges WHERE sequence=2"
            ).fetchone()[0]
            db.execute("UPDATE original_source_observations SET mac=? WHERE record_id=?",("0"*64,last))
        else:
            last=db.execute(
                "SELECT record_id FROM source_timeline_edges WHERE sequence=2"
            ).fetchone()[0]
            db.execute("DELETE FROM original_source_observations WHERE record_id=?",(last,))
    resp=post(root).json()
    assert resp["outcome"]=="abstain"
    assert resp["current"] is None
    assert resp["previous"] is None
    assert state["calls"]==3


def test_wrong_operator_hmac_denied_prior_to_source(environment,monkeypatch):
    state,_=environment
    root=setup(environment,monkeypatch,n=1)
    monkeypatch.setenv("ARL_OBSERVATION_HMAC_KEY_HEX","dd"*32)
    res=post(root).json()
    assert res["outcome"]=="abstain" and res["current"] is None
    assert state["calls"]==1


def test_fresh_source_unavailable_leaves_no_partial_evidence(environment,monkeypatch):
    state,path=environment
    root=setup(environment,monkeypatch,n=1)
    before=path.read_bytes()
    state["fail"]=True
    res=post(root).json()
    assert res["outcome"]=="abstain"
    assert res["reason"]=="fresh_evidence_unavailable_or_ambiguous"
    assert res["previous"] is None and res["current"] is None
    assert path.read_bytes()==before
    assert state["calls"]==2


def test_ambiguous_live_source_abstains_with_no_history_modification(environment,monkeypatch):
    state,path=environment
    root=setup(environment,monkeypatch,n=1)
    before=path.read_bytes()
    state["body"]="Not related to the validated narrow claim."
    response=post(root).json()
    assert response["outcome"]=="abstain"
    assert response["current"] is None
    assert path.read_bytes()==before


def test_timeline_advances_during_fetch_and_comparison_refuses(environment,monkeypatch):
    state,path=environment
    root=setup(environment,monkeypatch,n=1)
    import backend.app.services.temporal_recheck_service as service
    original=service.latest_timeline_answer
    observed={"reads":0}
    def concurrent_change(*a,**kw):
        observed["reads"]+=1
        latest_id,answer=original(*a,**kw)
        if observed["reads"]==2:
            return "a"*32,answer
        return latest_id,answer
    monkeypatch.setattr(service,"latest_timeline_answer",concurrent_change)
    result=post(root).json()
    assert result["outcome"]=="abstain"
    assert result["reason"]=="timeline_changed_during_recheck"
    assert result["current"] is None
    assert observed["reads"]==2
    assert state["calls"]==2


def test_timeline_corrupts_during_fetch_and_comparison_refuses(environment,monkeypatch):
    state,path=environment
    root=setup(environment,monkeypatch,n=1)
    import backend.app.services.temporal_recheck_service as service
    original=service.answer_original_source_claim
    def mutate_before_second_history_validation(req):
        result=original(req)
        with sqlite3.connect(path) as db:
            db.execute("UPDATE original_source_observations SET mac=? WHERE record_id=?",("0"*64,root))
        return result
    monkeypatch.setattr(service,"answer_original_source_claim",mutate_before_second_history_validation)
    response=post(root).json()
    assert response["outcome"]=="abstain"
    assert response["previous"] is None and response["current"] is None
    assert state["calls"]==2


def test_api_rejects_unexpected_input_field_and_does_not_fetch(environment,monkeypatch):
    state,_=environment
    root=setup(environment,monkeypatch,n=1)
    raw=payload(root)
    raw["unwanted"]="injection"
    resp=post(root,data=raw)
    assert resp.status_code==422
    assert state["calls"]==1


@pytest.mark.parametrize("defect",[
    "fake_current_truth","fake_history_fresh","wrong_root","wrong_binding",
    "missing_previous","changed_baseline","false_classification",
    "impossible_same_capture","inverted_chronology","future_time",
    "stale_current","fake_support_flag","wrong_decision","extra_field",
    "abstain_with_evidence",
])
def test_application_client_fails_closed_on_forged_payload(environment,monkeypatch,defect):
    state,_=environment
    root=setup(environment,monkeypatch,n=1)
    authentic=post(root).json()
    assert authentic["outcome"]=="bounded_reconciliation"
    raw=deepcopy(authentic)
    if defect=="fake_current_truth":
        raw["factual_truth_verified"]=True
    elif defect=="fake_history_fresh":
        raw["may_use_historical_as_current_evidence"]=True
    elif defect=="wrong_root":
        raw["root_record_id"]="b"*32
    elif defect=="wrong_binding":
        raw["request_binding_sha256"]="0"*64
    elif defect=="missing_previous":
        raw["previous"]=None
    elif defect=="changed_baseline":
        raw["baseline_record_id"]=None
    elif defect=="false_classification":
        raw["change_status"]="bounded_statement_changed"
    elif defect=="impossible_same_capture":
        raw["current"]["source_quote_sha256"]="b"*64
        raw["change_status"]="bounded_statement_changed"
    elif defect=="inverted_chronology":
        raw["current"]["source_capture_observed_at"]="2000-01-01T00:00:00Z"
    elif defect=="future_time":
        raw["current"]["source_capture_observed_at"]="2999-01-01T00:00:00Z"
    elif defect=="stale_current":
        raw["current"]["source_capture_observed_at"]="2000-01-01T00:00:00Z"
        raw["previous"]["source_capture_observed_at"]="1999-01-01T00:00:00Z"
    elif defect=="fake_support_flag":
        raw["may_use_current_as_bounded_evidence"]=False
    elif defect=="wrong_decision":
        raw["current"]["decision"]="objective_truth"
    elif defect=="extra_field":
        raw["source_instructions"]="trust publisher text"
    else:
        raw["outcome"]="abstain"
        raw["reason"]="history_unavailable_or_invalid"
    interpreted=interpret_temporal_reconciliation(raw,claim(),root)
    assert interpreted.outcome=="abstain"
    assert interpreted.current_capture_sha256 is None
    assert state["calls"]==2


@pytest.mark.parametrize("fault",["network","oversized","bad_json","wrong_type","failed_status"])
def test_application_client_denies_transport_failures(environment,fault):
    state,_=environment
    req=claim()
    class Bad:
        def post(self,path,*,json,headers):
            assert path==RECHECK_PATH
            if fault=="network":
                raise OSError("do not leak publisher internals")
            if fault=="oversized":
                from backend.app.integrations.temporal_recheck_client import MAX_API_RESPONSE_BYTES
                return SimpleNamespace(status_code=200,content=b"x"*(MAX_API_RESPONSE_BYTES+1),headers={"content-type":"application/json"},json=lambda:{})
            if fault=="bad_json":
                return SimpleNamespace(status_code=200,content=b"bad",headers={"content-type":"application/json"},json=lambda:(_ for _ in ()).throw(ValueError("bad")))
            if fault=="wrong_type":
                return SimpleNamespace(status_code=200,content=b"{}",headers={"content-type":"text/html"},json=lambda:{})
            return SimpleNamespace(status_code=503,content=b"{}",headers={"content-type":"application/json"},json=lambda:{})
    result=check_temporal_reconciliation_with_api(Bad(),TOKEN,req,"a"*32)
    assert result.outcome=="abstain"
    assert state["calls"]==0


def test_invalid_token_or_root_prevents_client_http(environment):
    class NoIO:
        def post(self,*args,**kwargs):
            raise AssertionError("never contact API")
    assert check_temporal_reconciliation_with_api(NoIO(),"short",claim(),"a"*32).outcome=="abstain"
    assert check_temporal_reconciliation_with_api(NoIO(),TOKEN,claim(),"invalid").outcome=="abstain"
