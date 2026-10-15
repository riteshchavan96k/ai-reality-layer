"""Step250 real authenticated original-source reconciliation smoke.

Three independently HTTPS-captured Python.org timeline observations are
persisted by separate CLI processes, then the on-demand API performs exactly
one new real HTTPS capture using the direct server-side verified-source path.
No historical storage writes or claims of actual publisher change.
"""
from __future__ import annotations

from hashlib import sha256
import json
import os
import secrets
import sys
import tempfile

from fastapi.testclient import TestClient

from backend.app.api.original_source_claim import OriginalSourceClaimRequest
from backend.app.evaluation.step247_live_history import _invoke, SOURCE, CLAIM
from backend.app.integrations.temporal_recheck_client import (
    RECHECK_PATH, check_temporal_reconciliation_with_api,
)
from backend.app.main import app
from backend.app.reality.allowlisted_https_source_reader import AllowlistedHttpsSourceReader


def main(argv: list[str]) -> int:
    if argv != ["--live"]:
        raise SystemExit("Step250 genuine HTTPS test requires explicit --live")
    with tempfile.TemporaryDirectory(prefix="arl-step250-") as directory:
        os.chmod(directory, 0o700)
        env = dict(os.environ)
        token=secrets.token_urlsafe(48)
        env.update({
            "ARL_RUNTIME_MODE":"pilot",
            "ARL_PILOT_BEARER_TOKEN":token,
            "ARL_INDEPENDENT_SOURCE_ALLOWED_URLS":json.dumps([SOURCE]),
            "ARL_OBSERVATION_STORE_PATH":os.path.join(directory,"timeline.sqlite3"),
            "ARL_OBSERVATION_HMAC_KEY_HEX":secrets.token_hex(32),
            "ARL_TEMPORAL_RECHECK_API_ENABLED":"1",
        })
        status,first=_invoke(env,"--live","--save-observation")
        if status!=0 or not isinstance(first,dict):
            raise RuntimeError("unable to save first real source observation")
        root=first["saved_record_id"]
        for number in (2,3):
            status,current=_invoke(env,"--live","--timeline-append",root)
            if (status!=0 or not isinstance(current,dict)
                or current.get("timeline_observation_count")!=number
                or current.get("recheck_status") not in (
                    "capture_unchanged","capture_changed_statement_unchanged",
                )):
                raise RuntimeError("real earlier timeline could not be verified")
        os.environ.update(env)
        path=env["ARL_OBSERVATION_STORE_PATH"]
        with open(path,"rb") as handle:
            before=sha256(handle.read()).hexdigest()
        original=AllowlistedHttpsSourceReader.__call__
        reads={"count":0}
        def counted(self,uri):
            reads["count"]+=1
            return original(self,uri)
        AllowlistedHttpsSourceReader.__call__=counted
        try:
            request=OriginalSourceClaimRequest(
                claim_text=CLAIM,entity="Python 3.13.0",source_uri=SOURCE,
                freshness_max_age_seconds=3600.0,
            )
            with TestClient(app) as http:
                result=check_temporal_reconciliation_with_api(http,token,request,root)
                if (result.outcome!="bounded_reconciliation"
                    or result.change_status not in (
                        "capture_unchanged","capture_changed_statement_unchanged",
                    ) or result.current_decision!="bounded_source_support"
                    or not result.may_use_current_as_bounded_evidence
                    or result.may_use_historical_as_current_evidence is not False
                    or result.factual_truth_verified is not False
                    or result.historical_receipt_authenticated is not False):
                    raise RuntimeError("live source and history could not be safely reconciled")
                denied=http.post(RECHECK_PATH,json={
                    "root_record_id":root,"claim":request.model_dump(mode="json"),
                })
                if denied.status_code!=401:
                    raise RuntimeError("missing bearer did not refuse reconciliation")
            with open(path,"rb") as handle:
                after=sha256(handle.read()).hexdigest()
            if before!=after or reads["count"]!=1:
                raise RuntimeError("reconciliation must fetch once and never alter stored history")
        finally:
            AllowlistedHttpsSourceReader.__call__=original
        print(json.dumps({
            "milestone":"step250_real_authenticated_live_to_history_reconciliation",
            "real_cli_source_observations":3,
            "new_live_source_observations_by_api":reads["count"],
            "read_only_history_unchanged":before==after,
            "conservative_reconciliation_succeeded":True,
            "missing_bearer_denied":True,
            "no_nested_self_http":True,
            "history_not_promoted_to_current_evidence":True,
            "external_deployment":False,
            "automatic_monitoring":False,
            "publisher_statement_change_proven":False,
            "publisher_authorship_verified":False,
            "factual_truth_verified":False,
        },sort_keys=True))
    return 0


if __name__=="__main__":
    raise SystemExit(main(sys.argv[1:]))
