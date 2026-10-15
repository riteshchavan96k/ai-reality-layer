"""Step247 adversarial local cross-invocation source history tests.

Source bodies here are MOCKED; the separate CI canary uses real Python.org TLS.
"""
from copy import deepcopy
from datetime import datetime, timezone
from hashlib import sha256
import json
import os
import sqlite3
import stat

import pytest

from backend.app.cli import EXIT_BOUNDED, EXIT_ABSTAIN, EXIT_REFUSED, run
from backend.app.reality.allowlisted_https_source_reader import AllowlistedHttpsSourceReader
from backend.app.integrations.source_history import (
    InvalidHistory, MAX_RECORDS, operator_history_configuration,
    load_verified_answer, save_verified_answer,
)
from backend.app.api.original_source_claim import OriginalSourceClaimRequest
from backend.app.integrations.cited_answer_client import check_cited_answer_with_api
from backend.app.main import app
from fastapi.testclient import TestClient

SOURCE = "https://www.python.org/downloads/release/python-3130/"
OFFLIST = "https://www.iana.org/domains/reserved"
TOKEN = "step247-private-local-operator-credential-do-not-log"
CLAIM = "Python 3.13.0 is a stable release."
POSITIVE = "This is the stable release of Python 3.13.0"
NEGATIVE = "Python 3.13.0 is not a stable release."
KEY = "a4" * 32


def snapshot(body=POSITIVE):
    return {
        "uri": SOURCE, "content": body,
        "capture_sha256": sha256(body.encode()).hexdigest(),
        "capture_observed_at": datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"),
        "observed_quote_unit_sha256": [],
    }


def args(*, claim=CLAIM, source=SOURCE, live=True):
    value = ["--claim", claim, "--entity", "Python 3.13.0", "--source", source]
    if live:
        value.append("--live")
    return value


@pytest.fixture
def environment(tmp_path, monkeypatch):
    os.chmod(tmp_path, 0o700)
    path = tmp_path / "private.sqlite3"
    monkeypatch.setenv("ARL_RUNTIME_MODE", "pilot")
    monkeypatch.setenv("ARL_PILOT_BEARER_TOKEN", TOKEN)
    monkeypatch.setenv("ARL_INDEPENDENT_SOURCE_ALLOWED_URLS", json.dumps([SOURCE]))
    monkeypatch.setenv("ARL_OBSERVATION_STORE_PATH", str(path))
    monkeypatch.setenv("ARL_OBSERVATION_HMAC_KEY_HEX", KEY)
    state = {"calls": 0, "body": POSITIVE, "fail": False}

    def fake_reader(self, uri):
        assert uri == SOURCE
        state["calls"] += 1
        if state["fail"]:
            raise OSError("secret untrusted publisher error")
        return deepcopy(snapshot(state["body"]))

    monkeypatch.setattr(AllowlistedHttpsSourceReader, "__call__", fake_reader)
    return state, path


def save():
    return run(args() + ["--save-observation"])


def recheck(record, **kw):
    return run(args(**kw) + ["--recheck-record", record])


def test_two_separate_cli_invocations_reopen_same_database(environment):
    state, path = environment
    code, first = save()
    assert code == EXIT_BOUNDED
    record = first["saved_record_id"]
    assert len(record) == 32 and path.exists()
    assert first["historical_receipt_authenticated"] is False
    assert first["factual_truth_verified"] is False
    assert first["citations"][0]["source_uri"] == SOURCE
    assert "untrusted_original_source_quote" not in first["citations"][0]
    assert not (stat.S_IMODE(path.stat().st_mode) & 0o077)
    code, current = recheck(record)
    assert code == EXIT_BOUNDED
    assert current["recheck_status"] == "capture_unchanged"
    assert len(current["observations"]) == 2
    assert "untrusted_original_source_quote" not in current["observations"][0]
    assert current["historical_receipt_authenticated"] is False
    assert current["factual_truth_verified"] is False
    assert state["calls"] == 2


def test_different_raw_capture_same_bounded_statement(environment):
    state, _ = environment
    _, first = save()
    state["body"] = POSITIVE + "\nAdditional unambiguous metadata"
    code, current = recheck(first["saved_record_id"])
    assert code == EXIT_BOUNDED
    assert current["recheck_status"] == "capture_changed_statement_unchanged"
    assert state["calls"] == 2


def test_real_bounded_statement_change_to_contradiction(environment):
    state, _ = environment
    _, first = save()
    state["body"] = NEGATIVE
    code, current = recheck(first["saved_record_id"])
    assert code == EXIT_BOUNDED
    assert current["recheck_status"] == "bounded_statement_changed"
    assert current["current_decision"] == "bounded_source_contradiction"
    assert current["may_use_as_bounded_evidence"] is False


@pytest.mark.parametrize("defect", ["body", "mac", "truncate", "remove"])
def test_tampered_local_history_abstains_prior_to_any_source_egress(environment, defect):
    state, path = environment
    _, first = save()
    record = first["saved_record_id"]
    with sqlite3.connect(path) as database:
        if defect == "body":
            database.execute(
                "UPDATE original_source_observations SET payload=? WHERE record_id=?",
                ('{"version":1}', record),
            )
        elif defect == "mac":
            database.execute(
                "UPDATE original_source_observations SET mac=? WHERE record_id=?",
                ("0" * 64, record),
            )
        elif defect == "truncate":
            database.execute(
                "UPDATE original_source_observations SET payload=? WHERE record_id=?",
                ("x" * 12000, record),
            )
        else:
            database.execute("DELETE FROM original_source_observations WHERE record_id=?", (record,))
    code, result = recheck(record)
    assert code == EXIT_ABSTAIN and result is None
    assert state["calls"] == 1


def test_wrong_operator_key_refuses_to_use_history(environment, monkeypatch):
    state, _ = environment
    _, first = save()
    monkeypatch.setenv("ARL_OBSERVATION_HMAC_KEY_HEX", "b5" * 32)
    code, result = recheck(first["saved_record_id"])
    assert code == EXIT_ABSTAIN and result is None
    assert state["calls"] == 1


def test_record_cannot_be_replayed_for_changed_claim(environment):
    state, _ = environment
    _, first = save()
    code, result = recheck(first["saved_record_id"], claim=NEGATIVE)
    assert code == EXIT_ABSTAIN and result is None
    assert state["calls"] == 1


@pytest.mark.parametrize("invalid_id", ["", "0" * 31, "../history", "X" * 32, "0" * 33])
def test_invalid_record_ids_are_inert(environment, invalid_id):
    state, _ = environment
    code, result = recheck(invalid_id)
    assert code == EXIT_ABSTAIN and result is None
    assert state["calls"] == 0


def test_source_failure_suppresses_both_historical_and_current_citations(environment):
    state, _ = environment
    _, first = save()
    state["fail"] = True
    code, result = recheck(first["saved_record_id"])
    assert code == EXIT_ABSTAIN
    assert result["observations"] == []
    assert first["saved_record_id"] not in json.dumps(result)
    assert POSITIVE not in json.dumps(result)
    assert TOKEN not in json.dumps(result)


@pytest.mark.parametrize("mode", ["save", "recheck"])
def test_explicit_live_optin_required_without_source_request(environment, mode):
    state, _ = environment
    operation = ["--save-observation"] if mode == "save" else ["--recheck-record", "0" * 32]
    code, result = run(args(live=False) + operation)
    assert code == EXIT_REFUSED and result is None and state["calls"] == 0


@pytest.mark.parametrize("mode", ["save", "recheck"])
def test_offlist_source_rejected_before_history_or_source_egress(environment, mode):
    state, _ = environment
    operation = ["--save-observation"] if mode == "save" else ["--recheck-record", "0" * 32]
    code, result = run(args(source=OFFLIST) + operation)
    assert code == EXIT_REFUSED and result is None and state["calls"] == 0


def test_recheck_cannot_mix_two_hosts(environment):
    state, _ = environment
    code, result = run(args() + ["--source", OFFLIST, "--recheck-record", "0" * 32])
    assert code == EXIT_REFUSED and result is None and state["calls"] == 0


def test_absent_key_refused_before_egress(environment, monkeypatch):
    state, _ = environment
    monkeypatch.delenv("ARL_OBSERVATION_HMAC_KEY_HEX")
    code, result = save()
    assert code == EXIT_REFUSED and result is None and state["calls"] == 0


def test_missing_private_store_directory_refused_before_egress(environment, monkeypatch, tmp_path):
    state, _ = environment
    monkeypatch.setenv("ARL_OBSERVATION_STORE_PATH", str(tmp_path / "missing" / "db.sqlite3"))
    code, result = save()
    assert code == EXIT_REFUSED and result is None and state["calls"] == 0


def test_world_readable_directory_refused_before_egress(environment, tmp_path):
    state, _ = environment
    os.chmod(tmp_path, 0o755)
    try:
        code, result = save()
        assert code == EXIT_REFUSED and result is None and state["calls"] == 0
    finally:
        os.chmod(tmp_path, 0o700)


def test_world_readable_database_refused_before_egress(environment):
    state, path = environment
    _, first = save()
    os.chmod(path, 0o644)
    code, result = recheck(first["saved_record_id"])
    assert code == EXIT_REFUSED and result is None and state["calls"] == 1


def test_sqlite_file_symlink_rejected(environment, tmp_path, monkeypatch):
    state, path = environment
    real = tmp_path / "real.sqlite3"
    real.write_text("do not write")
    path.symlink_to(real)
    code, result = save()
    assert code == EXIT_REFUSED and result is None and state["calls"] == 0
    assert real.read_text() == "do not write"


def test_invalid_initial_observation_is_never_saved(environment):
    state, path = environment
    state["body"] = "An unrelated publisher paragraph."
    code, report = save()
    assert code == EXIT_ABSTAIN
    assert report["citations"] == []
    assert "saved_record_id" not in report
    with sqlite3.connect(path) as db:
        assert db.execute("SELECT COUNT(*) FROM original_source_observations").fetchone()[0] == 0


def test_optional_untrusted_quote_is_explicitly_labeled(environment):
    _, _ = environment
    code, first = run(args() + ["--save-observation", "--include-untrusted-quotes"])
    assert code == EXIT_BOUNDED
    assert first["citations"][0]["untrusted_original_source_quote"] == POSITIVE


def test_capacity_refuses_overwrite_and_does_not_claim_save(environment, monkeypatch):
    import backend.app.integrations.source_history as history
    monkeypatch.setattr(history, "MAX_RECORDS", 1)
    _, first = save()
    code, result = save()
    assert code == EXIT_ABSTAIN and result is None
    code, current = recheck(first["saved_record_id"])
    assert code == EXIT_BOUNDED and len(current["observations"]) == 2


def test_valid_mac_does_not_mean_independently_authenticated_history(environment):
    _, _ = environment
    code, first = save()
    assert code == EXIT_BOUNDED
    path, key = operator_history_configuration()
    request = OriginalSourceClaimRequest(claim_text=CLAIM, entity="Python 3.13.0", source_uri=SOURCE)
    stored = load_verified_answer(path, key, first["saved_record_id"], request)
    assert stored.factual_truth_verified is False
    assert stored.publisher_authorship_verified is False
    assert stored.citation.original_source_quote == POSITIVE


def test_saved_mode_must_not_run_with_recheck_flag(environment):
    state, _ = environment
    with pytest.raises(SystemExit):
        run(args() + ["--save-observation", "--recheck"])
    assert state["calls"] == 0
