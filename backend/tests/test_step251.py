"""Step251 separately authorized, idempotent API timeline lifecycle adversarial tests.

Publisher readings are mocked; CI separately checks genuine Python.org HTTPS.
"""
from copy import deepcopy
from datetime import datetime, timezone
import json
import os
import sqlite3
from types import SimpleNamespace

import pytest
from fastapi.testclient import TestClient

from backend.tests.test_step247 import (
    environment, SOURCE, OFFLIST, TOKEN, POSITIVE, NEGATIVE, KEY,
)
from backend.app.api.original_source_claim import OriginalSourceClaimRequest
from backend.app.integrations.temporal_timeline_write_client import (
    CREATE_PATH, APPEND_PATH, write_timeline_with_api, interpret_timeline_write,
)
from backend.app.integrations.temporal_timeline_client import check_temporal_timeline_with_api
from backend.app.integrations.temporal_recheck_client import check_temporal_reconciliation_with_api
from backend.app.integrations.source_history import InvalidHistory
from backend.app.main import app

WRITER = "step251-independent-private-write-credential-kept-out-of-results"
A = "a1"*16
B = "b2"*16
C = "c3"*16
D = "d4"*16


@pytest.fixture
def owner(environment, monkeypatch):
    state, path = environment
    monkeypatch.setenv("ARL_TIMELINE_WRITE_API_ENABLED", "1")
    monkeypatch.setenv("ARL_TIMELINE_WRITE_TOKEN", WRITER)
    monkeypatch.setenv("ARL_TEMPORAL_HISTORY_API_ENABLED", "1")
    monkeypatch.setenv("ARL_TEMPORAL_RECHECK_API_ENABLED", "1")
    return state, path


def claim(text="Python 3.13.0 is a stable release.", source=SOURCE):
    return OriginalSourceClaimRequest(
        claim_text=text, entity="Python 3.13.0",
        source_uri=source, freshness_max_age_seconds=3600.0,
    )


def headers(*, bearer=TOKEN, writer=WRITER):
    result = {"Authorization": "Bearer " + bearer}
    if writer is not None:
        result["X-ARL-Timeline-Write-Token"] = writer
    return result


def create(*, op=A, bearer=TOKEN, writer=WRITER, request=None):
    with TestClient(app) as http:
        return http.post(
            CREATE_PATH, json={
                "operation_id": op,
                "claim": (request or claim()).model_dump(mode="json"),
            }, headers=headers(bearer=bearer, writer=writer),
        )


def append(root, expected, *, op=B, bearer=TOKEN, writer=WRITER, request=None):
    with TestClient(app) as http:
        return http.post(
            APPEND_PATH, json={
                "operation_id": op, "root_record_id": root,
                "expected_latest_record_id": expected,
                "claim": (request or claim()).model_dump(mode="json"),
            }, headers=headers(bearer=bearer, writer=writer),
        )


def count(path):
    if not path.exists():
        return 0
    with sqlite3.connect(path) as db:
        return db.execute("SELECT COUNT(*) FROM original_source_observations").fetchone()[0]


def create_baseline():
    response=create()
    assert response.status_code==200, response.text
    info=response.json()
    assert info["outcome"]=="created", info
    assert info["root_record_id"]==info["record_id"]
    assert info["sequence"]==0
    assert info["change_status"]=="baseline"
    return info["root_record_id"]


def test_complete_api_create_append_inspect_recheck_and_replay(owner):
    state, path = owner
    with TestClient(app) as client:
        first=write_timeline_with_api(client,TOKEN,WRITER,claim(),A)
        assert first.outcome=="created"
        assert first.sequence==0 and first.change_status=="baseline"
        assert first.factual_truth_verified is False
        assert first.may_use_historical_as_current_evidence is False
        root=first.root_record_id
        assert root==first.record_id
        first_repeat=write_timeline_with_api(client,TOKEN,WRITER,claim(),A)
        assert first_repeat.replayed is True and first_repeat.record_id==root
        assert state["calls"]==1

        second=write_timeline_with_api(client,TOKEN,WRITER,claim(),B,root=root,expected=root)
        assert second.outcome=="appended" and second.sequence==1
        assert second.change_status=="capture_unchanged"
        again=write_timeline_with_api(client,TOKEN,WRITER,claim(),B,root=root,expected=root)
        assert again.replayed is True and again.record_id==second.record_id
        assert state["calls"]==2

        state["body"]=POSITIVE+"\nExtra release-site metadata"
        third=write_timeline_with_api(client,TOKEN,WRITER,claim(),C,root=root,expected=second.record_id)
        assert third.outcome=="appended" and third.sequence==2
        assert third.change_status=="capture_changed_statement_unchanged"
        after_new_head=write_timeline_with_api(client,TOKEN,WRITER,claim(),B,root=root,expected=root)
        assert after_new_head.replayed is True
        assert after_new_head.record_id==second.record_id
        assert state["calls"]==3

        timeline=check_temporal_timeline_with_api(client,TOKEN,claim(),root)
        assert timeline.outcome=="verified_historical_timeline"
        assert timeline.latest_record_id==third.record_id
        assert len(timeline.observations)==3
        assert state["calls"]==3
        live=check_temporal_reconciliation_with_api(client,TOKEN,claim(),root)
        assert live.outcome=="bounded_reconciliation"
        assert live.change_status=="capture_unchanged"
        assert state["calls"]==4
    assert count(path)==3
    with sqlite3.connect(path) as db:
        assert db.execute("SELECT count(*) FROM timeline_write_operations").fetchone()[0]==3
        assert db.execute("SELECT count(*) FROM source_timeline_edges").fetchone()[0]==3
    assert WRITER not in json.dumps(third.__dict__) and TOKEN not in json.dumps(first.__dict__)


def test_bounded_statement_change_support_to_contradiction(owner):
    state,_=owner
    root=create_baseline()
    state["body"]=NEGATIVE
    res=append(root,root).json()
    assert res["outcome"]=="appended"
    assert res["change_status"]=="bounded_statement_changed"
    assert res["decision"]=="bounded_source_contradiction"
    assert res["factual_truth_verified"] is False
    assert state["calls"]==2


@pytest.mark.parametrize("writer", [None, TOKEN, "invalid-writer-token", WRITER+"x"])
def test_reader_cannot_write_without_independent_write_credential(owner, writer):
    state,path=owner
    response=create(writer=writer)
    assert response.status_code==403
    assert not path.exists() and state["calls"]==0


def test_reader_can_still_read_without_write_credential(owner):
    state,_=owner
    root=create_baseline()
    with TestClient(app) as client:
        response=client.post(
            "/api/v1/reality-state/timeline",
            json={"root_record_id":root,"claim":claim().model_dump(mode="json")},
            headers={"Authorization":"Bearer "+TOKEN},
        )
    assert response.status_code==200
    assert response.json()["outcome"]=="verified_historical_timeline"


def test_writer_credential_alone_never_bypasses_pilot_bearer(owner):
    state,path=owner
    result=create(bearer=WRITER)
    assert result.status_code==401
    assert not path.exists() and state["calls"]==0


def test_write_mode_disabled_by_default_protects_storage(owner,monkeypatch):
    state,path=owner
    monkeypatch.delenv("ARL_TIMELINE_WRITE_API_ENABLED")
    assert create().status_code==403
    assert not path.exists() and state["calls"]==0


@pytest.mark.parametrize("broken",["short","same_reader","missing"])
def test_write_secret_invalid_configuration_fail_closed(owner,monkeypatch,broken):
    state,path=owner
    if broken=="short":monkeypatch.setenv("ARL_TIMELINE_WRITE_TOKEN","short")
    elif broken=="same_reader":monkeypatch.setenv("ARL_TIMELINE_WRITE_TOKEN",TOKEN)
    else:monkeypatch.delenv("ARL_TIMELINE_WRITE_TOKEN")
    assert create().status_code==503
    assert not path.exists() and state["calls"]==0


def test_development_mode_does_not_enable_writer(owner,monkeypatch):
    state,path=owner
    monkeypatch.setenv("ARL_RUNTIME_MODE","development")
    monkeypatch.delenv("ARL_PILOT_BEARER_TOKEN")
    assert create().status_code==503
    assert not path.exists() and state["calls"]==0


@pytest.mark.parametrize("source", [OFFLIST])
def test_offlist_never_fetches_or_persists(owner,source):
    state,path=owner
    res=create(request=claim(source=source))
    assert res.status_code==200 and res.json()["outcome"]=="abstain"
    assert state["calls"]==0 and count(path)==0


def test_invalid_api_payload_rejected_without_io(owner):
    state,path=owner
    with TestClient(app) as client:
        response=client.post(CREATE_PATH,json={
            "operation_id":A,"claim":claim().model_dump(mode="json"),
            "client_supplied_quote":"Injected authority",
        },headers=headers())
    assert response.status_code==422
    assert state["calls"]==0 and not path.exists()


@pytest.mark.parametrize("bad", ["no id", "A"*32, "0"*31, "../other"])
def test_invalid_operation_id_rejected_before_io(owner,bad):
    state,path=owner
    res=create(op=bad)
    assert res.status_code==422
    assert state["calls"]==0 and not path.exists()


def test_reusing_operation_id_for_different_claim_denied_without_source_read(owner):
    state,path=owner
    root=create_baseline()
    res=create(op=A,request=claim(text=NEGATIVE))
    assert res.json()["outcome"]=="abstain"
    assert res.json()["record_id"] is None
    assert count(path)==1 and state["calls"]==1


def test_reusing_operation_id_for_another_kind_denied_without_source_read(owner):
    state,path=owner
    root=create_baseline()
    res=append(root,root,op=A)
    assert res.json()["outcome"]=="abstain"
    assert res.json()["record_id"] is None
    assert state["calls"]==1


def test_stale_append_refused_without_source_egress(owner):
    state,path=owner
    root=create_baseline()
    first=append(root,root).json()
    assert first["outcome"]=="appended"
    stale=append(root,root,op=C).json()
    assert stale["outcome"]=="abstain"
    assert stale["record_id"] is None
    assert count(path)==2 and state["calls"]==2


def test_wrong_claim_or_source_append_refused_without_source_read(owner):
    state,path=owner
    root=create_baseline()
    bad=append(root,root,request=claim(text=NEGATIVE)).json()
    assert bad["outcome"]=="abstain"
    source_bad=append(root,root,op=C,request=claim(source=OFFLIST)).json()
    assert source_bad["outcome"]=="abstain"
    assert count(path)==1 and state["calls"]==1


@pytest.mark.parametrize("kind",["create","append"])
def test_source_failure_does_not_create_partial_historical_receipt(owner,kind):
    state,path=owner
    root=create_baseline() if kind=="append" else None
    before=count(path)
    state["fail"]=True
    resp=(create(op=C) if kind=="create" else append(root,root)).json()
    assert resp["outcome"]=="abstain"
    assert resp["record_id"] is None and resp["root_record_id"] is None
    assert count(path)==before
    assert TOKEN not in json.dumps(resp) and WRITER not in json.dumps(resp)


@pytest.mark.parametrize("defect",["mac","edge","missing"])
def test_tampered_timeline_denied_prior_to_source_fetch(owner,defect):
    state,path=owner
    root=create_baseline()
    second=append(root,root).json()
    rec=second["record_id"]
    with sqlite3.connect(path) as db:
        if defect=="mac":db.execute("UPDATE original_source_observations SET mac=? WHERE record_id=?",("0"*64,rec))
        elif defect=="edge":db.execute("UPDATE source_timeline_edges SET edge_mac=? WHERE sequence=1",("0"*64,))
        else:db.execute("DELETE FROM original_source_observations WHERE record_id=?",(rec,))
    denied=append(root,rec,op=C).json()
    assert denied["outcome"]=="abstain"
    assert denied["record_id"] is None and state["calls"]==2


def test_tampered_operation_receipt_denied_prior_to_source_egress(owner):
    state,path=owner
    root=create_baseline()
    with sqlite3.connect(path) as db:
        db.execute("UPDATE timeline_write_operations SET mac=? WHERE operation_id=?",("0"*64,A))
    denied=create().json()
    assert denied["outcome"]=="abstain"
    assert denied["record_id"] is None and state["calls"]==1


def test_operator_key_mismatch_denies_replay_and_append(owner,monkeypatch):
    state,path=owner
    root=create_baseline()
    monkeypatch.setenv("ARL_OBSERVATION_HMAC_KEY_HEX","b5"*32)
    assert create().json()["outcome"]=="abstain"
    assert append(root,root).json()["outcome"]=="abstain"
    assert state["calls"]==1


def test_atomic_create_rollback_on_idempotency_index_failure(owner,monkeypatch):
    state,path=owner
    import backend.app.integrations.source_timeline_writes as writes
    def explode(*args):
        raise InvalidHistory("injected commit failure")
    monkeypatch.setattr(writes,"_register",explode)
    result=create().json()
    assert result["outcome"]=="abstain"
    assert result["record_id"] is None
    assert count(path)==0


def test_atomic_append_rollback_on_idempotency_index_failure(owner,monkeypatch):
    state,path=owner
    root=create_baseline()
    import backend.app.integrations.source_timeline_writes as writes
    def explode(*args):
        raise InvalidHistory("injected commit failure")
    monkeypatch.setattr(writes,"_register",explode)
    result=append(root,root).json()
    assert result["outcome"]=="abstain"
    assert count(path)==1
    with sqlite3.connect(path) as db:
        assert db.execute("SELECT count(*) FROM source_timeline_edges").fetchone()[0]==0


def test_storage_limit_never_commits_half_operation(owner,monkeypatch):
    state,path=owner
    root=create_baseline()
    import backend.app.integrations.source_timeline_writes as writes
    monkeypatch.setattr(writes,"MAX_OPERATIONS",1)
    result=append(root,root).json()
    assert result["outcome"]=="abstain"
    assert count(path)==1
    with sqlite3.connect(path) as db:
        assert db.execute("SELECT count(*) FROM timeline_write_operations").fetchone()[0]==1
        assert db.execute("SELECT count(*) FROM source_timeline_edges").fetchone()[0]==0


def test_concurrent_stale_writer_rejected_inside_transaction(owner,monkeypatch):
    state,path=owner
    root=create_baseline()
    import backend.app.services.temporal_timeline_write_service as service
    original=service._capture
    def change_during_fetch(req):
        # Do not recursively intercept the second writer's own source read.
        monkeypatch.setattr(service,"_capture",original)
        fresh=original(req)
        concurrent=append(root,root,op=C).json()
        assert concurrent["outcome"]=="appended"
        return fresh
    monkeypatch.setattr(service,"_capture",change_during_fetch)
    denied=append(root,root,op=B).json()
    assert denied["outcome"]=="abstain"
    assert count(path)==2
    with sqlite3.connect(path) as db:
        assert db.execute("SELECT count(*) FROM timeline_write_operations").fetchone()[0]==2


@pytest.mark.parametrize("defect",[
    "fake_truth","wrong_binding","wrong_op","wrong_record","bad_sequence",
    "wrong_baseline","wrong_status","unexpected_extra","fake_replay","future_time",
    "abstain_with_record",
])
def test_defensive_client_rejects_corrupted_receipts(owner,defect):
    state,path=owner
    root=create_baseline()
    saved=create().json()
    data=deepcopy(saved)
    if defect=="fake_truth":data["factual_truth_verified"]=True
    elif defect=="wrong_binding":data["request_binding_sha256"]="0"*64
    elif defect=="wrong_op":data["operation_id"]=B
    elif defect=="wrong_record":data["record_id"]=B
    elif defect=="bad_sequence":data["sequence"]=1
    elif defect=="wrong_baseline":data["change_status"]="capture_unchanged"
    elif defect=="wrong_status":data["outcome"]="appended"
    elif defect=="unexpected_extra":data["hidden_authority"]=True
    elif defect=="fake_replay":data["replayed"]=0
    elif defect=="future_time":data["source_capture_observed_at"]="2999-01-01T00:00:00Z"
    else:data["outcome"]="abstain";data["reason"]="history_unavailable_or_invalid"
    outcome=interpret_timeline_write(data,claim(),A)
    assert outcome.outcome=="abstain"
    assert outcome.record_id is None
    assert state["calls"]==1


@pytest.mark.parametrize("failure",["network","response_error","wrong_type","huge","bad_json"])
def test_defensive_client_denies_transport_failures_without_retry(owner,failure):
    state,_=owner
    class BrokenTransport:
        def post(self,path,*,json,headers):
            assert path==CREATE_PATH
            if failure=="network":raise ConnectionError("secret never returned")
            if failure=="response_error":return SimpleNamespace(status_code=503,content=b"{}",headers={"content-type":"application/json"},json=lambda:{})
            if failure=="wrong_type":return SimpleNamespace(status_code=200,content=b"{}",headers={"content-type":"text/html"},json=lambda:{})
            if failure=="huge":
                from backend.app.integrations.ai_claim_gate import MAX_API_RESPONSE_BYTES
                return SimpleNamespace(status_code=200,content=b"x"*(MAX_API_RESPONSE_BYTES+1),headers={"content-type":"application/json"},json=lambda:{})
            return SimpleNamespace(status_code=200,content=b"no",headers={"content-type":"application/json"},json=lambda:(_ for _ in ()).throw(ValueError("bad")))
    result=write_timeline_with_api(BrokenTransport(),TOKEN,WRITER,claim(),A)
    assert result.outcome=="abstain" and result.record_id is None
    assert state["calls"]==0


def test_client_invalid_tokens_refuses_request_before_transport(owner):
    class NoHTTP:
        def post(self,*args,**kwargs):
            raise AssertionError("should not send")
    assert write_timeline_with_api(NoHTTP(),TOKEN,"weak",claim(),A).outcome=="abstain"
    assert write_timeline_with_api(NoHTTP(),"weak",WRITER,claim(),A).outcome=="abstain"
    assert write_timeline_with_api(NoHTTP(),TOKEN,WRITER,claim(),"invalid").outcome=="abstain"
