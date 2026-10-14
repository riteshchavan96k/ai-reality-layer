"""Step245 real fixed original HTTPS -> local operator CLI -> bounded citation.

Use --live only. No public hosting, customer authentication beyond configured
local pilot, real dual-publisher support claim, model inference, arbitrary URL,
or credential/source-text logging. Always redact raw JSON evidence in audit.
"""
from __future__ import annotations

import argparse
from contextlib import redirect_stdout, redirect_stderr
from io import StringIO
import json
import os
import secrets
from unittest.mock import patch

from backend.app.cli import EXIT_ABSTAIN, EXIT_BOUNDED, EXIT_REFUSED, main
from backend.app.reality.allowlisted_https_source_reader import AllowlistedHttpsSourceReader

PYTHON = "https://www.python.org/downloads/release/python-3130/"
IANA = "https://www.iana.org/domains/reserved"
OFFLIST = "https://go.dev/dl/"
CLAIM = "Python 3.13.0 is a stable release."
ENTITY = "Python 3.13.0"


def _invoke(urls: list[str], *, quotes=False, live=True):
    argv = ["--claim", CLAIM, "--entity", ENTITY]
    for url in urls:
        argv.extend(["--source", url])
    if live:
        argv.append("--live")
    if quotes:
        argv.append("--include-untrusted-quotes")
    stdout = StringIO()
    stderr = StringIO()
    with redirect_stdout(stdout), redirect_stderr(stderr):
        code = main(argv)
    # No content from source/error or credentials is ever printed here.
    return code, json.loads(stdout.getvalue()) if stdout.getvalue() else None, stderr.getvalue()


def run_live() -> dict:
    token = secrets.token_urlsafe(48)
    env = {
        "ARL_RUNTIME_MODE": "pilot",
        "ARL_PILOT_BEARER_TOKEN": token,
        "ARL_INDEPENDENT_SOURCE_ALLOWED_URLS": json.dumps([PYTHON, IANA]),
    }
    original = AllowlistedHttpsSourceReader.__call__
    reads = []

    def observed(self, uri):
        reads.append(uri)
        return original(self, uri)

    with patch.dict(os.environ, env), patch.object(
        AllowlistedHttpsSourceReader, "__call__", observed
    ):
        first, one, first_error = _invoke([PYTHON], quotes=True)
        second, two, second_error = _invoke([PYTHON, IANA], quotes=True)
        before_blocked = list(reads)
        no_optin, no_data, opt_error = _invoke([PYTHON], live=False)
        offlist, off_data, off_error = _invoke([PYTHON, OFFLIST])
        after_blocked = list(reads)

    if not (
        first == EXIT_BOUNDED
        and one is not None
        and one["decision"] == "bounded_source_support"
        and one["may_use_as_bounded_evidence"] is True
        and len(one["citations"]) == 1
        and one["citations"][0]["source_uri"] == PYTHON
        and one["citations"][0]["untrusted_original_source_quote"]
            == "This is the stable release of Python 3.13.0"
        and second == EXIT_ABSTAIN
        and two is not None
        and two["decision"] == "abstain"
        and two["citations"] == []
        and two["may_use_as_bounded_evidence"] is False
        and no_optin == EXIT_REFUSED and no_data is None
        and offlist == EXIT_REFUSED and off_data is None
        and before_blocked == [PYTHON, PYTHON, IANA]
        and after_blocked == before_blocked
        and not first_error and not second_error
        and token not in opt_error + off_error
        and all(
            result["factual_truth_verified"] is False
            and result["publisher_authorship_verified"] is False
            and result["independently_owned_publishers_verified"] is False
            and result["general_question_answering"] is False
            and result["neural_model_used"] is False
            for result in (one, two)
        )
    ):
        raise RuntimeError("local developer CLI original HTTPS proof failed")

    return {
        "milestone": "step245_actual_source_to_local_operator_cli",
        "genuine_python_org_single_source_citation": True,
        "genuine_two_distinct_https_host_refusal": True,
        "authenticated_local_pilot": True,
        "opt_in_required": True,
        "unapproved_second_source_blocked_before_network": True,
        "raw_publisher_data_or_credentials_logged": False,
        "real_dual_source_positive_corroboration_proven": False,
        "factual_truth_verified": False,
        "publisher_independence_proven": False,
        "externally_deployed": False,
    }


def cli(argv=None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--live", action="store_true")
    args = parser.parse_args(argv)
    if not args.live:
        parser.error("genuine fixed HTTPS canary requires --live")
    try:
        print(json.dumps(run_live(), sort_keys=True))
        return 0
    except Exception:
        print("Step245 actual local operator CLI acceptance failed")
        return 1


if __name__ == "__main__":
    raise SystemExit(cli())
