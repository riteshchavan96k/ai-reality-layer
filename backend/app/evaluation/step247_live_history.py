"""Step247 actual independent CLI subprocesses and publisher HTTPS observations.

No fabricated historical change: captures are seconds apart and are never
presented as independent evidence of publisher-authenticated chronology.
"""
from __future__ import annotations

import json
import os
import pathlib
import secrets
import subprocess
import sys
import tempfile


SOURCE = "https://www.python.org/downloads/release/python-3130/"
OFFLIST = "https://www.iana.org/domains/reserved"
CLAIM = "Python 3.13.0 is a stable release."


def _invoke(env: dict[str, str], *mode: str) -> tuple[int, dict | None]:
    argv = [
        sys.executable, "-m", "backend.app.cli", "--claim", CLAIM,
        "--entity", "Python 3.13.0", "--source", SOURCE, *mode,
    ]
    result = subprocess.run(
        argv, env=env, cwd=pathlib.Path(__file__).resolve().parents[3],
        capture_output=True, text=True, timeout=75, check=False,
    )
    if result.returncode not in (0, 2, 3) or len(result.stdout) > 16000:
        raise RuntimeError("local original-source CLI failed")
    if result.returncode != 0:
        if result.stdout.strip():
            raise RuntimeError("denied source returned unexpected data")
        return result.returncode, None
    try:
        return result.returncode, json.loads(result.stdout)
    except (ValueError, TypeError) as exc:
        raise RuntimeError("invalid original-source report") from exc


def main(argv: list[str]) -> int:
    if argv != ["--live"]:
        raise SystemExit("explicit --live required")
    with tempfile.TemporaryDirectory(prefix="arl-step247-") as directory:
        os.chmod(directory, 0o700)
        env = dict(os.environ)
        env.update({
            "ARL_RUNTIME_MODE": "pilot",
            "ARL_PILOT_BEARER_TOKEN": secrets.token_urlsafe(48),
            "ARL_INDEPENDENT_SOURCE_ALLOWED_URLS": json.dumps([SOURCE]),
            "ARL_OBSERVATION_STORE_PATH": os.path.join(directory, "history.sqlite3"),
            "ARL_OBSERVATION_HMAC_KEY_HEX": secrets.token_hex(32),
        })
        denied, missing_optin = _invoke(env, "--save-observation")
        if denied != 3 or missing_optin is not None:
            raise RuntimeError("missing consent was not denied")
        status, first = _invoke(env, "--live", "--save-observation")
        if status != 0 or not isinstance(first, dict):
            raise RuntimeError("first authenticated HTTPS observation failed")
        record_id = first.get("saved_record_id")
        if not isinstance(record_id, str) or len(record_id) != 32:
            raise RuntimeError("durable first observation was not saved")
        if first.get("decision") != "bounded_source_support":
            raise RuntimeError("first publisher observation not bounded aligned")
        if first.get("factual_truth_verified") is not False:
            raise RuntimeError("unsupported factual truth flag")
        if not os.path.isfile(env["ARL_OBSERVATION_STORE_PATH"]):
            raise RuntimeError("durable store file not created")

        # A new Python process opens the signed historical record, makes one
        # new live HTTPS request and compares the two captures.
        second_status, second = _invoke(
            env, "--live", "--recheck-record", record_id,
        )
        if second_status != 0 or not isinstance(second, dict):
            raise RuntimeError("cross-process original-source recheck failed")
        if second.get("recheck_status") not in (
            "capture_unchanged", "capture_changed_statement_unchanged",
        ):
            raise RuntimeError("bounded original-source statement differed")
        if second.get("previous_decision") != "bounded_source_support":
            raise RuntimeError("incorrect historical source decision")
        if second.get("current_decision") != "bounded_source_support":
            raise RuntimeError("current publisher statement not aligned")
        if len(second.get("observations", [])) != 2:
            raise RuntimeError("source observations missing")
        if second.get("historical_receipt_authenticated") is not False:
            raise RuntimeError("historical truth was incorrectly certified")
        if second.get("factual_truth_verified") is not False:
            raise RuntimeError("objective truth was incorrectly certified")
        if any("untrusted_original_source_quote" in c for c in second["observations"]):
            raise RuntimeError("publisher quotation leaked by default")

        failed, missing = _invoke(env, "--live", "--recheck-record", "0" * 32)
        if failed != 2 or missing is not None:
            raise RuntimeError("unknown history must fail closed")

        print(json.dumps({
            "milestone": "step247_real_two_process_persistent_source_history",
            "live_https_source_reads": 2,
            "separate_cli_processes": 2,
            "private_database_saved_and_reopened": True,
            "operator_hmac_verified": True,
            "denied_non_live_without_egress": True,
            "missing_history_refused": True,
            "historical_receipt_independently_attested": False,
            "real_world_truth_verified": False,
            "publisher_authorship_verified": False,
            "externally_deployed": False,
            "automatic_monitoring_enabled": False,
            "publisher_change_proven": False,
            "raw_source_or_secrets_logged": False,
        }, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
