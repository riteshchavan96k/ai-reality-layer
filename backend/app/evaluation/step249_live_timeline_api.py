"""Step249 genuinely populated cross-process history -> read-only FastAPI -> strict AI client.

Initial capture and two append operations use genuine Python.org HTTPS. A
separate authenticated TestClient consumes that durable timeline without
fetching sources or modifying the database. No publisher-change assertion.
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
from backend.app.integrations.temporal_timeline_client import (
    TIMELINE_PATH, check_temporal_timeline_with_api,
)
from backend.app.main import app
from backend.app.reality.allowlisted_https_source_reader import AllowlistedHttpsSourceReader


def main(argv: list[str]) -> int:
    if argv != ["--live"]:
        raise SystemExit("explicit --live required for live setup")
    with tempfile.TemporaryDirectory(prefix="arl-step249-") as directory:
        os.chmod(directory, 0o700)
        env = dict(os.environ)
        token = secrets.token_urlsafe(48)
        env.update({
            "ARL_RUNTIME_MODE": "pilot",
            "ARL_PILOT_BEARER_TOKEN": token,
            "ARL_INDEPENDENT_SOURCE_ALLOWED_URLS": json.dumps([SOURCE]),
            "ARL_OBSERVATION_STORE_PATH": os.path.join(directory, "history.sqlite3"),
            "ARL_OBSERVATION_HMAC_KEY_HEX": secrets.token_hex(32),
            "ARL_TEMPORAL_HISTORY_API_ENABLED": "1",
        })
        status, saved = _invoke(env, "--live", "--save-observation")
        if status != 0 or not isinstance(saved, dict):
            raise RuntimeError("real original-source history baseline did not save")
        root = saved["saved_record_id"]
        ids = [root]
        for expected_count in (2, 3):
            status, latest = _invoke(env, "--live", "--timeline-append", root)
            if (
                status != 0 or not isinstance(latest, dict)
                or latest.get("timeline_observation_count") != expected_count
                or latest.get("recheck_status") not in (
                    "capture_unchanged", "capture_changed_statement_unchanged",
                )
            ):
                raise RuntimeError("real authenticated source recheck could not append")
            ids.append(latest["appended_record_id"])
        os.environ.update(env)
        db_path = env["ARL_OBSERVATION_STORE_PATH"]
        with open(db_path, "rb") as f:
            database_before = sha256(f.read()).hexdigest()
        calls = {"egress": 0}
        original_reader = AllowlistedHttpsSourceReader.__call__

        def refuse_any_fetch(self, uri):
            calls["egress"] += 1
            raise AssertionError("temporal-history API must be strictly offline")

        AllowlistedHttpsSourceReader.__call__ = refuse_any_fetch
        try:
            request = OriginalSourceClaimRequest(
                claim_text=CLAIM, entity="Python 3.13.0",
                source_uri=SOURCE, freshness_max_age_seconds=3600.0,
            )
            with TestClient(app) as client:
                result = check_temporal_timeline_with_api(client, token, request, root)
                assert result.outcome == "verified_historical_timeline"
                assert [row.record_id for row in result.observations] == ids
                assert result.latest_record_id == ids[-1]
                assert result.may_use_as_current_evidence is False
                assert result.historical_receipt_authenticated is False
                assert result.factual_truth_verified is False
                assert result.publisher_authorship_verified is False
                assert result.automatic_monitoring_enabled is False
                direct = client.post(
                    TIMELINE_PATH, json={
                        "claim": request.model_dump(mode="json"),
                        "root_record_id": root,
                    }, headers={"Authorization": "Bearer " + token},
                )
                assert direct.status_code == 200
                assert direct.headers["Cache-Control"] == "no-store"
                assert direct.json()["outcome"] == "verified_historical_timeline"
                assert direct.json()["timeline"]["total_observations"] == 3
                assert "original_source_quote" not in json.dumps(direct.json())
                denied = client.post(TIMELINE_PATH, json={
                    "claim": request.model_dump(mode="json"), "root_record_id": root,
                })
                assert denied.status_code == 401
            with open(db_path, "rb") as f:
                database_after = sha256(f.read()).hexdigest()
            if database_before != database_after or calls["egress"] != 0:
                raise RuntimeError("historical API read must not modify DB or fetch source")
        finally:
            AllowlistedHttpsSourceReader.__call__ = original_reader
        print(json.dumps({
            "milestone": "step249_real_three_capture_history_to_authenticated_timeline_api",
            "real_https_source_reads_during_explicit_cli_setup": 3,
            "separate_source_observation_processes": 3,
            "authenticated_app_client_returned_three_historical_observations": True,
            "api_history_read_source_egress": calls["egress"],
            "api_history_read_database_unchanged": database_before == database_after,
            "missing_bearer_denied": True,
            "historical_receipt_independently_attested": False,
            "factual_truth_verified": False,
            "may_use_as_current_evidence": False,
            "externally_deployed": False,
            "automatic_monitoring_enabled": False,
            "publisher_change_proven": False,
        }, sort_keys=True))
        return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
