"""Step246: exactly two genuine Python.org HTTPS captures via local operator CLI.

One explicit --live invocation, no arbitrary URLs, model, historical database,
publishing claims, secrets, source bodies, or digest values in workflow logs.
"""
from __future__ import annotations

import argparse
import json
import os
import secrets
from unittest.mock import patch

from backend.app.cli import EXIT_BOUNDED, EXIT_REFUSED, run
from backend.app.reality.allowlisted_https_source_reader import AllowlistedHttpsSourceReader

SOURCE = "https://www.python.org/downloads/release/python-3130/"
UNAPPROVED = "https://go.dev/dl/"


def _arguments(source: str, *, live: bool = True):
    args = [
        "--claim", "Python 3.13.0 is a stable release.",
        "--entity", "Python 3.13.0", "--source", source, "--recheck",
    ]
    if live:
        args.append("--live")
    return args


def run_live() -> dict:
    token = secrets.token_urlsafe(48)
    env = {
        "ARL_RUNTIME_MODE": "pilot",
        "ARL_PILOT_BEARER_TOKEN": token,
        "ARL_INDEPENDENT_SOURCE_ALLOWED_URLS": json.dumps([SOURCE]),
    }
    seen = []
    original = AllowlistedHttpsSourceReader.__call__

    def measured(self, url):
        seen.append(url)
        return original(self, url)

    with patch.dict(os.environ, env), patch.object(
        AllowlistedHttpsSourceReader, "__call__", measured
    ):
        completed, result = run(_arguments(SOURCE))
        count = len(seen)
        no_optin, none = run(_arguments(SOURCE, live=False))
        unauthorized, none_other = run(_arguments(UNAPPROVED))
        final_count = len(seen)

    if not (
        completed == EXIT_BOUNDED
        and result is not None
        and result["recheck_status"] in (
            "capture_unchanged", "capture_changed_statement_unchanged",
        )
        and result["scope"] == "two_observations_of_one_original_source"
        and result["previous_decision"] == "bounded_source_support"
        and result["current_decision"] == "bounded_source_support"
        and result["may_use_as_bounded_evidence"] is True
        and result["historical_receipt_authenticated"] is False
        and result["automatic_monitoring_enabled"] is False
        and result["factual_truth_verified"] is False
        and result["publisher_authorship_verified"] is False
        and result["independently_owned_publishers_verified"] is False
        and len(result["observations"]) == 2
        and all(row["source_uri"] == SOURCE for row in result["observations"])
        and all(
            "untrusted_original_source_quote" not in row
            for row in result["observations"]
        )
        and [row["role"] for row in result["observations"]] == ["previous", "current"]
        and count == 2
        and seen == [SOURCE, SOURCE]
        and final_count == count
        and no_optin == EXIT_REFUSED and none is None
        and unauthorized == EXIT_REFUSED and none_other is None
    ):
        raise RuntimeError("Step246 original HTTPS two-capture recheck failed")
    # Never print source quotes, capture digests, timestamps, URLs, token.
    return {
        "milestone": "step246_real_original_https_temporal_recheck",
        "real_https_source_reads": 2,
        "authenticated_local_cli": True,
        "source_capture_comparison_completed": True,
        "current_bounded_source_statement_still_aligned": True,
        "no_optin_or_offlist_source_read": True,
        "raw_source_text_or_secrets_logged": False,
        "historical_receipt_authenticated": False,
        "automatic_background_monitoring": False,
        "real_world_truth_verified": False,
        "publisher_authorship_verified": False,
        "externally_deployed": False,
    }


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--live", action="store_true")
    args = parser.parse_args(argv)
    if not args.live:
        parser.error("real HTTPS explicitly requires --live")
    try:
        print(json.dumps(run_live(), sort_keys=True))
        return 0
    except Exception:
        print("Step246 genuine original HTTPS recheck canary failed")
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
