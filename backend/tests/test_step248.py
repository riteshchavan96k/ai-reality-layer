"""Step248 longitudinal Reality State timeline adversarial tests.

Sources are deliberately mocked. The separate real HTTPS canary must prove
three independent Python processes can persist and inspect a timeline.
"""
from copy import deepcopy
from hashlib import sha256
import json
import os
import sqlite3
from datetime import datetime, timezone

import pytest
from fastapi.testclient import TestClient

from backend.tests.test_step247 import (
    environment, args, save, SOURCE, NEGATIVE, POSITIVE, KEY, OFFLIST,
)
from backend.app.cli import EXIT_BOUNDED, EXIT_ABSTAIN, EXIT_REFUSED, run
from backend.app.api.original_source_claim import OriginalSourceClaimRequest
from backend.app.integrations.source_history import InvalidHistory, operator_history_configuration
from backend.app.integrations.source_timeline import (
    latest_timeline_answer, inspect_timeline, append_verified_recheck,
)
from backend.app.integrations.source_recheck import recheck_cited_answer_with_api
from backend.app.main import app


def timeline_args(root, *, mode="--timeline-append", live=True, claim=None):
    out = args(claim=claim or "Python 3.13.0 is a stable release.", live=live)
    return out + [mode, root]


def baseline():
    status, response = save()
    assert status == EXIT_BOUNDED
    return response["saved_record_id"]


def append(root):
    return run(timeline_args(root))


def show(root, *, live=False):
    return run(timeline_args(root, mode="--timeline-show", live=live))


def test_first_second_third_observations_and_latest_reuse(environment):
    state, path = environment
    root = baseline()
    code, report = show(root)
    assert code == EXIT_BOUNDED
    assert report["total_observations"] == 1
    assert report["linked_history"] is False
    assert report["latest_record_id"] == root
    assert state["calls"] == 1  # offline timeline is not a source read

    code, second = append(root)
    assert code == EXIT_BOUNDED
    assert second["recheck_status"] == "capture_unchanged"
    assert second["timeline_observation_count"] == 2
    assert second["timeline_root_id"] == root
    record2 = second["appended_record_id"]
    assert record2 != root

    state["body"] = POSITIVE + "\nAdditional unambiguous metadata"
    code, third = append(root)
    assert code == EXIT_BOUNDED
    assert third["recheck_status"] == "capture_changed_statement_unchanged"
    assert third["timeline_observation_count"] == 3
    record3 = third["appended_record_id"]
    assert record3 not in (root, record2)

    code, timeline = show(root)
    assert code == EXIT_BOUNDED
    assert timeline["total_observations"] == 3
    assert timeline["latest_record_id"] == record3
    assert timeline["linked_history"] is True
    assert [row["record_id"] for row in timeline["observations"]] == [root, record2, record3]
    assert [row["change_from_previous"] for row in timeline["observations"]] == [
        "baseline", "capture_unchanged", "capture_changed_statement_unchanged",
    ]
    assert state["calls"] == 3
    assert "untrusted_original_source_quote" not in json.dumps(timeline)
    assert POSITIVE not in json.dumps(timeline)
    assert timeline["factual_truth_verified"] is False
    assert timeline["historical_receipt_authenticated"] is False


def test_bounded_source_decision_reversal_is_historical_not_truth(environment):
    state, path = environment
    root = baseline()
    state["body"] = NEGATIVE
    code, second = append(root)
    assert code == EXIT_BOUNDED
    assert second["recheck_status"] == "bounded_statement_changed"
    assert second["current_decision"] == "bounded_source_contradiction"
    assert second["may_use_as_bounded_evidence"] is False
    code, report = show(root)
    assert code == EXIT_BOUNDED
    assert report["observations"][-1]["decision"] == "bounded_source_contradiction"
    state["body"] = POSITIVE
    code, third = append(root)
    assert code == EXIT_BOUNDED
    assert third["previous_decision"] == "bounded_source_contradiction"
    assert third["current_decision"] == "bounded_source_support"
    assert state["calls"] == 3


def test_failed_fresh_read_does_not_append_or_reveal_previous(environment):
    state, path = environment
    root = baseline()
    state["fail"] = True
    code, report = append(root)
    assert code == EXIT_ABSTAIN
    assert report["observations"] == []
    assert "appended_record_id" not in report
    assert POSITIVE not in json.dumps(report)
    code, timeline = show(root)
    assert code == EXIT_BOUNDED
    assert timeline["total_observations"] == 1
    with sqlite3.connect(path) as db:
        assert db.execute("SELECT COUNT(*) FROM original_source_observations").fetchone()[0] == 1
        assert db.execute("SELECT COUNT(*) FROM source_timeline_edges").fetchone()[0] == 0


@pytest.mark.parametrize("defect", ["edge_mac", "edge_seq", "edge_parent", "edge_status", "child_payload", "missing_child"])
def test_corrupt_linked_history_abstains_before_source_egress(environment, defect):
    state, path = environment
    root = baseline()
    code, first = append(root)
    assert code == EXIT_BOUNDED
    rec2 = first["appended_record_id"]
    with sqlite3.connect(path) as db:
        if defect == "edge_mac":
            db.execute("UPDATE source_timeline_edges SET edge_mac=? WHERE sequence=1", ("0"*64,))
        elif defect == "edge_seq":
            db.execute("UPDATE source_timeline_edges SET sequence=10 WHERE sequence=1")
        elif defect == "edge_parent":
            db.execute("UPDATE source_timeline_edges SET previous_id=? WHERE sequence=1", ("a"*32,))
        elif defect == "edge_status":
            db.execute("UPDATE source_timeline_edges SET change_status='bogus' WHERE sequence=1")
        elif defect == "child_payload":
            db.execute("UPDATE original_source_observations SET payload='{}' WHERE record_id=?", (rec2,))
        else:
            db.execute("DELETE FROM original_source_observations WHERE record_id=?", (rec2,))
    code, result = append(root)
    assert code == EXIT_ABSTAIN and result is None
    code, result = show(root)
    assert code == EXIT_ABSTAIN and result is None
    assert state["calls"] == 2


def test_record_replay_across_claims_is_denied_before_egress(environment):
    state, _ = environment
    root = baseline()
    code, result = run(timeline_args(root, claim=NEGATIVE))
    assert code == EXIT_ABSTAIN and result is None
    assert state["calls"] == 1


def test_wrong_hmac_key_denies_timeline_before_source_egress(environment, monkeypatch):
    state, _ = environment
    root = baseline()
    code, _ = append(root)
    assert code == EXIT_BOUNDED
    monkeypatch.setenv("ARL_OBSERVATION_HMAC_KEY_HEX", "b5"*32)
    code, result = append(root)
    assert code == EXIT_ABSTAIN and result is None
    assert state["calls"] == 2


def test_unknown_root_denied_without_source_reads(environment):
    state, _ = environment
    code, result = append("f"*32)
    assert code == EXIT_ABSTAIN and result is None
    assert state["calls"] == 0


def test_offline_inspection_requires_authenticated_local_source_policy(environment, monkeypatch):
    state, _ = environment
    root = baseline()
    monkeypatch.delenv("ARL_PILOT_BEARER_TOKEN")
    code, result = show(root)
    assert code == EXIT_REFUSED and result is None
    assert state["calls"] == 1


def test_inspection_never_calls_source_even_with_live_flag(environment):
    state, _ = environment
    root = baseline()
    code, result = show(root, live=True)
    assert code == EXIT_BOUNDED
    assert result["total_observations"] == 1
    assert state["calls"] == 1


@pytest.mark.parametrize("mode", ["--timeline-append", "--timeline-show"])
def test_refuses_two_sources_or_offlist(environment, mode):
    state, _ = environment
    root = baseline()
    argv = args() + ["--source", OFFLIST, mode, root]
    code, data = run(argv)
    assert code == EXIT_REFUSED and data is None
    code, data = run(args(source=OFFLIST) + [mode, root])
    assert code == EXIT_REFUSED and data is None
    assert state["calls"] == 1


def test_append_requires_explicit_network_optin(environment):
    state, _ = environment
    root = baseline()
    code, result = run(timeline_args(root, live=False))
    assert code == EXIT_REFUSED and result is None
    assert state["calls"] == 1


def test_stale_concurrent_writer_cannot_commit_and_no_orphan_record(environment):
    state, path = environment
    root = baseline()
    store, key = operator_history_configuration()
    req = OriginalSourceClaimRequest(
        claim_text="Python 3.13.0 is a stable release.",
        entity="Python 3.13.0", source_uri=SOURCE,
        freshness_max_age_seconds=3600.0,
    )
    previous_id, previous = latest_timeline_answer(store, key, root, req)
    with TestClient(app) as client:
        comparison = recheck_cited_answer_with_api(client, os.environ["ARL_PILOT_BEARER_TOKEN"], req, previous)
    assert comparison.status == "capture_unchanged"
    new_id, n = append_verified_recheck(store, key, root, req, previous_id, comparison)
    assert n == 2
    with pytest.raises(InvalidHistory):
        append_verified_recheck(store, key, root, req, previous_id, comparison)
    with sqlite3.connect(path) as db:
        assert db.execute("SELECT COUNT(*) FROM original_source_observations").fetchone()[0] == 2
        assert db.execute("SELECT COUNT(*) FROM source_timeline_edges").fetchone()[0] == 2
    assert state["calls"] == 2


def test_mid_commit_failure_rolls_back_edge_and_source_record(environment, monkeypatch):
    state, path = environment
    root = baseline()
    import backend.app.integrations.source_timeline as timeline
    original = timeline._edge_mac
    def break_edge(key, root_id, seq, rec, parent, status):
        if seq == 1:
            raise InvalidHistory("simulated failure, secret should not leak")
        return original(key, root_id, seq, rec, parent, status)
    monkeypatch.setattr(timeline, "_edge_mac", break_edge)
    code, out = append(root)
    assert code == EXIT_ABSTAIN and out is None
    with sqlite3.connect(path) as db:
        assert db.execute("SELECT COUNT(*) FROM original_source_observations").fetchone()[0] == 1
        assert db.execute("SELECT COUNT(*) FROM source_timeline_edges").fetchone()[0] == 0
    assert state["calls"] == 2


def test_timeline_limit_preflight_prevents_extra_source_fetch(environment, monkeypatch):
    state, path = environment
    root = baseline()
    import backend.app.integrations.source_timeline as timeline
    monkeypatch.setattr(timeline, "MAX_TIMELINE_OBSERVATIONS", 2)
    code, second = append(root)
    assert code == EXIT_BOUNDED
    code, third = append(root)
    assert code == EXIT_ABSTAIN and third is None
    assert state["calls"] == 2
    code, report = show(root)
    assert code == EXIT_BOUNDED and report["total_observations"] == 2


def test_explicitly_valid_keyed_but_falsified_change_status_rejected(environment):
    state, path = environment
    root = baseline()
    _, second = append(root)
    import backend.app.integrations.source_timeline as timeline
    with sqlite3.connect(path) as db:
        rid=second["appended_record_id"]
        db.execute(
            "UPDATE source_timeline_edges SET change_status=?,edge_mac=? WHERE sequence=1",
            ("bounded_statement_changed",
             timeline._edge_mac(bytes.fromhex(KEY), root, 1, rid, root, "bounded_statement_changed")),
        )
    code, report = show(root)
    assert code == EXIT_ABSTAIN and report is None
    assert state["calls"] == 2
