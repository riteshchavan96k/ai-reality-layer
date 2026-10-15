"""Step248 real local three-observation timeline, across independent CLI processes.

Uses original HTTPS Python.org via the existing authenticated local pilot.
Controlled changed-publisher assertions exist exclusively in unit tests.
"""
from __future__ import annotations

import json
import os
import secrets
import sys
import tempfile

from backend.app.evaluation.step247_live_history import _invoke, SOURCE


def main(argv: list[str]) -> int:
    if argv != ["--live"]:
        raise SystemExit("real timeline smoke requires explicit --live")
    with tempfile.TemporaryDirectory(prefix="arl-step248-") as directory:
        os.chmod(directory, 0o700)
        env = dict(os.environ)
        env.update({
            "ARL_RUNTIME_MODE": "pilot",
            "ARL_PILOT_BEARER_TOKEN": secrets.token_urlsafe(48),
            "ARL_INDEPENDENT_SOURCE_ALLOWED_URLS": json.dumps([SOURCE]),
            "ARL_OBSERVATION_STORE_PATH": os.path.join(directory, "evidence.sqlite3"),
            "ARL_OBSERVATION_HMAC_KEY_HEX": secrets.token_hex(32),
        })
        status, first = _invoke(env, "--live", "--save-observation")
        if status != 0 or not isinstance(first, dict):
            raise RuntimeError("initial real HTTPS source observation failed")
        root = first.get("saved_record_id")
        if not isinstance(root, str) or len(root) != 32:
            raise RuntimeError("missing durable initial record")

        # Separate subprocesses make one HTTPS request per append and exit.
        ids = [root]
        for expected_count in (2, 3):
            status, current = _invoke(env, "--live", "--timeline-append", root)
            if status != 0 or not isinstance(current, dict):
                raise RuntimeError("real cross-session source timeline append failed")
            if (
                current.get("timeline_observation_count") != expected_count
                or current.get("timeline_root_id") != root
                or current.get("recheck_status") not in (
                    "capture_unchanged", "capture_changed_statement_unchanged",
                )
                or current.get("current_decision") != "bounded_source_support"
                or current.get("factual_truth_verified") is not False
            ):
                raise RuntimeError("unexpected bounded source-recheck result")
            record = current.get("appended_record_id")
            if not isinstance(record, str) or len(record) != 32 or record in ids:
                raise RuntimeError("invalid appended observation identifier")
            ids.append(record)

        # Deliberately omit --live: offline inspection must never fetch source.
        status, timeline = _invoke(env, "--timeline-show", root)
        if status != 0 or not isinstance(timeline, dict):
            raise RuntimeError("offline timeline inspection failed")
        observations = timeline.get("observations", [])
        if (
            timeline.get("total_observations") != 3
            or timeline.get("latest_record_id") != ids[-1]
            or [row.get("record_id") for row in observations] != ids
            or timeline.get("linked_history") is not True
            or timeline.get("factual_truth_verified") is not False
            or timeline.get("historical_receipt_authenticated") is not False
            or timeline.get("automatic_monitoring_enabled") is not False
            or any("untrusted_original_source_quote" in row for row in observations)
        ):
            raise RuntimeError("unexpected operator-held longitudinal evidence report")

        denied, _ = _invoke(env, "--timeline-append", root)
        if denied != 3:
            raise RuntimeError("append without explicit --live was not denied")
        missing, _ = _invoke(env, "--live", "--timeline-append", "0" * 32)
        if missing != 2:
            raise RuntimeError("unknown historical root did not abstain")

        print(json.dumps({
            "milestone": "step248_live_longitudinal_source_timeline",
            "real_https_source_reads": 3,
            "independent_capture_and_append_processes": 3,
            "read_only_offline_inspection_process": True,
            "private_sqlite_observation_count": 3,
            "keyed_timeline_integrity_verified": True,
            "latest_baseline_advanced_twice": True,
            "no_live_append_refused": True,
            "unknown_root_abstained_before_egress": True,
            "publisher_authorship_verified": False,
            "historical_timestamp_independently_verified": False,
            "factual_truth_verified": False,
            "publisher_statement_change_proven": False,
            "externally_deployed": False,
            "automatic_background_monitoring": False,
        }, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
