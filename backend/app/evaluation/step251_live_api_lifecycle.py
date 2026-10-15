"""Step251 real authenticated application-only history lifecycle over Python.org.

Two explicit source reads create and append an operator-keyed timeline through
the REST API, an independently authenticated read-only client reads it, and a
separate live reconciliation reads a third HTTPS source. No CLI mutation used.
"""
from __future__ import annotations

import json
import os
import secrets
import sys
import tempfile

from fastapi.testclient import TestClient

from backend.app.api.original_source_claim import OriginalSourceClaimRequest
from backend.app.evaluation.step247_live_history import SOURCE, CLAIM
from backend.app.integrations.temporal_timeline_client import check_temporal_timeline_with_api
from backend.app.integrations.temporal_timeline_write_client import (
    write_timeline_with_api, CREATE_PATH, APPEND_PATH,
)
from backend.app.integrations.temporal_recheck_client import check_temporal_reconciliation_with_api
from backend.app.main import app
from backend.app.reality.allowlisted_https_source_reader import AllowlistedHttpsSourceReader


def main(argv: list[str]) -> int:
    if argv != ["--live"]:
        raise SystemExit("Step251 genuine HTTPS lifecycle requires explicit --live")
    with tempfile.TemporaryDirectory(prefix="arl-step251-") as directory:
        os.chmod(directory, 0o700)
        token=secrets.token_urlsafe(48)
        writer=secrets.token_urlsafe(48)
        while writer == token:
            writer=secrets.token_urlsafe(48)
        db_path=os.path.join(directory,"api-history.sqlite3")
        env=dict(os.environ)
        env.update({
            "ARL_RUNTIME_MODE":"pilot",
            "ARL_PILOT_BEARER_TOKEN":token,
            "ARL_INDEPENDENT_SOURCE_ALLOWED_URLS":json.dumps([SOURCE]),
            "ARL_OBSERVATION_STORE_PATH":db_path,
            "ARL_OBSERVATION_HMAC_KEY_HEX":secrets.token_hex(32),
            "ARL_TIMELINE_WRITE_API_ENABLED":"1",
            "ARL_TIMELINE_WRITE_TOKEN":writer,
            "ARL_TEMPORAL_HISTORY_API_ENABLED":"1",
            "ARL_TEMPORAL_RECHECK_API_ENABLED":"1",
        })
        os.environ.update(env)
        original=AllowlistedHttpsSourceReader.__call__
        source_reads={"count":0}
        def counted(self,uri):
            source_reads["count"]+=1
            return original(self,uri)
        AllowlistedHttpsSourceReader.__call__=counted
        try:
            request=OriginalSourceClaimRequest(
                claim_text=CLAIM, entity="Python 3.13.0",
                source_uri=SOURCE, freshness_max_age_seconds=3600.0,
            )
            op_create=secrets.token_hex(16)
            op_append=secrets.token_hex(16)
            with TestClient(app) as http:
                initial=write_timeline_with_api(http,token,writer,request,op_create)
                if initial.outcome!="created" or initial.sequence!=0:
                    raise RuntimeError("authenticated API failed to persist initial genuine source")
                root=initial.root_record_id
                first_again=write_timeline_with_api(http,token,writer,request,op_create)
                if not first_again.replayed or first_again.record_id!=root or source_reads["count"]!=1:
                    raise RuntimeError("API create retry performed unexpected external source read")

                second=write_timeline_with_api(
                    http,token,writer,request,op_append,root=root,expected=root,
                )
                if (second.outcome!="appended" or second.sequence!=1
                    or second.change_status not in (
                        "capture_unchanged","capture_changed_statement_unchanged"
                    ) or source_reads["count"]!=2):
                    raise RuntimeError("API did not atomically append verified source observation")
                replay=write_timeline_with_api(
                    http,token,writer,request,op_append,root=root,expected=root,
                )
                if not replay.replayed or replay.record_id!=second.record_id or source_reads["count"]!=2:
                    raise RuntimeError("append retry produced unexpected history or network read")

                read=check_temporal_timeline_with_api(http,token,request,root)
                if (
                    read.outcome!="verified_historical_timeline"
                    or len(read.observations)!=2
                    or read.latest_record_id!=second.record_id
                    or source_reads["count"]!=2
                    or read.may_use_as_current_evidence is not False
                ):
                    raise RuntimeError("Step249 application could not consume Step251-created history")

                # Reader bearer without independent writer authorization cannot mutate.
                denied=http.post(CREATE_PATH,json={
                    "operation_id":secrets.token_hex(16),
                    "claim":request.model_dump(mode="json"),
                },headers={"Authorization":"Bearer "+token})
                if denied.status_code!=403 or source_reads["count"]!=2:
                    raise RuntimeError("read-only bearer wrongly authorized for write")

                stale=write_timeline_with_api(
                    http,token,writer,request,secrets.token_hex(16),
                    root=root,expected=root,
                )
                if stale.outcome!="abstain" or source_reads["count"]!=2:
                    raise RuntimeError("stale latest-record precondition not enforced")

                current=check_temporal_reconciliation_with_api(http,token,request,root)
                if (
                    current.outcome!="bounded_reconciliation"
                    or current.change_status not in (
                        "capture_unchanged","capture_changed_statement_unchanged"
                    ) or source_reads["count"]!=3
                    or current.may_use_historical_as_current_evidence is not False
                ):
                    raise RuntimeError("Step250 did not reconcile the genuinely API-created timeline")

                final=check_temporal_timeline_with_api(http,token,request,root)
                if final.latest_record_id!=second.record_id or len(final.observations)!=2:
                    raise RuntimeError("read-only source recheck silently mutated timeline")
            print(json.dumps({
                "milestone":"step251_real_original_source_api_only_lifecycle",
                "genuine_python_org_https_observations":source_reads["count"],
                "api_created_history_without_cli":True,
                "api_appended_history_without_cli":True,
                "replayed_create_without_egress":True,
                "replayed_append_without_egress":True,
                "reader_without_writer_denied":True,
                "stale_expected_head_denied_before_egress":True,
                "step249_read_history_verified":True,
                "step250_recheck_of_api_history_verified":True,
                "history_not_modified_by_read_or_recheck":True,
                "publisher_authorship_verified":False,
                "real_world_truth_verified":False,
                "automatic_monitoring":False,
                "external_deployment":False,
            },sort_keys=True))
        finally:
            AllowlistedHttpsSourceReader.__call__=original
    return 0


if __name__=="__main__":
    raise SystemExit(main(sys.argv[1:]))
