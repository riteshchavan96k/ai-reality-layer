"""Step245 first runnable developer/operator claim-check workflow via real local API.

Positive/conflict sources below are explicitly MOCKED; real HTTPS is tested
separately in step245_live_cli.py and does not certify factual truth.
"""
from copy import deepcopy
from datetime import datetime, timedelta, timezone
from hashlib import sha256
import json

import pytest

from backend.app.cli import (
    EXIT_ABSTAIN, EXIT_BOUNDED, EXIT_INTERNAL, EXIT_REFUSED, main, run,
)
from backend.app.reality.allowlisted_https_source_reader import AllowlistedHttpsSourceReader

PYTHON = "https://www.python.org/downloads/release/python-3130/"
IANA = "https://www.iana.org/domains/reserved"
UNAPPROVED = "https://go.dev/dl/"
TOKEN = "step245-cli-test-only-bearer-longer-than-32-printable"
POSITIVE = "This is the stable release of Python 3.13.0"
NEGATIVE = "Python 3.13.0 is not a stable release."


def capture(uri, text=POSITIVE, *, observed=None, quote_hashes=None):
    return {
        "uri": uri, "content": text,
        "capture_sha256": sha256(text.encode("utf-8")).hexdigest(),
        "capture_observed_at": (observed or datetime.now(timezone.utc))
            .isoformat().replace("+00:00", "Z"),
        "observed_quote_unit_sha256": quote_hashes or [],
    }


def args(*sources, claim="Python 3.13.0 is a stable release.", live=True,
         quotes=False, age=3600):
    argv = ["--claim", claim, "--entity", "Python 3.13.0"]
    for source_uri in sources or (PYTHON,):
        argv += ["--source", source_uri]
    argv += ["--max-age", str(age)]
    if live:
        argv.append("--live")
    if quotes:
        argv.append("--include-untrusted-quotes")
    return argv


@pytest.fixture
def pilot(monkeypatch):
    monkeypatch.setenv("ARL_RUNTIME_MODE", "pilot")
    monkeypatch.setenv("ARL_PILOT_BEARER_TOKEN", TOKEN)
    monkeypatch.setenv("ARL_INDEPENDENT_SOURCE_ALLOWED_URLS", json.dumps([PYTHON, IANA]))
    reads = []
    records = {PYTHON: capture(PYTHON), IANA: capture(IANA)}

    def instrumented(self, uri):
        reads.append(uri)
        item = records[uri]
        if isinstance(item, Exception):
            raise item
        return deepcopy(item)

    monkeypatch.setattr(AllowlistedHttpsSourceReader, "__call__", instrumented)
    return reads, records


def verify_ceiling(report):
    for name in (
        "factual_truth_verified", "publisher_authorship_verified",
        "independently_owned_publishers_verified", "general_question_answering",
        "neural_model_used",
    ):
        assert report[name] is False


def test_single_source_genuine_api_client_positive_with_machine_readable_citation(pilot):
    reads, _ = pilot
    status, report = run(args(PYTHON))
    assert status == EXIT_BOUNDED
    assert report["decision"] == "bounded_source_support"
    assert report["reason_code"] == "source_aligned"
    assert report["may_use_as_bounded_evidence"] is True
    assert len(report["citations"]) == 1
    assert report["citations"][0]["source_uri"] == PYTHON
    assert report["citations"][0]["source_quote_sha256"] == sha256(POSITIVE.encode()).hexdigest()
    assert "untrusted_original_source_quote" not in report["citations"][0]
    assert reads == [PYTHON]
    verify_ceiling(report)


def test_explicit_quote_opt_in_is_untrusted_json_data_not_an_assertion(pilot, capsys):
    code = main(args(PYTHON, quotes=True))
    report = json.loads(capsys.readouterr().out)
    assert code == EXIT_BOUNDED
    assert report["citations"][0]["untrusted_original_source_quote"] == POSITIVE
    assert "factual_truth_verified" in report and report["factual_truth_verified"] is False
    assert TOKEN not in json.dumps(report)


def test_single_source_contradiction_is_observed_but_never_truth(pilot):
    reads, records = pilot
    records[PYTHON] = capture(PYTHON, NEGATIVE)
    status, report = run(args(PYTHON))
    assert status == EXIT_BOUNDED
    assert report["decision"] == "bounded_source_contradiction"
    assert report["may_use_as_bounded_evidence"] is False
    assert len(report["citations"]) == 1
    assert reads == [PYTHON]


def test_two_source_mocked_agreement_via_real_local_api_and_both_client_citations(pilot):
    reads, _ = pilot
    status, report = run(args(PYTHON, IANA))
    assert status == EXIT_BOUNDED
    assert report["decision"] == "two_source_alignment"
    assert report["may_use_as_bounded_evidence"] is True
    assert report["distinct_https_hostnames"] is True
    assert [c["source_uri"] for c in report["citations"]] == [PYTHON, IANA]
    assert reads == [PYTHON, IANA]
    verify_ceiling(report)


@pytest.mark.parametrize("negative_url", [PYTHON, IANA])
def test_two_source_disagreement_cannot_allow_supported_decision(pilot, negative_url):
    reads, records = pilot
    records[negative_url] = capture(negative_url, NEGATIVE)
    status, report = run(args(PYTHON, IANA))
    assert status == EXIT_BOUNDED
    assert report["decision"] == "source_disagreement"
    assert report["may_use_as_bounded_evidence"] is False
    assert len(report["citations"]) == 2
    assert reads == [PYTHON, IANA]


def test_two_source_mocked_contradictions_are_bounded_and_not_supported(pilot):
    reads, records = pilot
    records[PYTHON] = capture(PYTHON, NEGATIVE)
    records[IANA] = capture(IANA, NEGATIVE)
    status, report = run(args(PYTHON, IANA))
    assert status == EXIT_BOUNDED
    assert report["decision"] == "two_source_contradiction"
    assert report["may_use_as_bounded_evidence"] is False
    assert reads == [PYTHON, IANA]


def test_unsupported_claim_causes_no_source_read_or_citation(pilot):
    reads, _ = pilot
    status, report = run(args(PYTHON, claim="Maybe Python 3.13.0 is stable."))
    assert status == EXIT_ABSTAIN
    assert report["decision"] == "abstain"
    assert report["citations"] == []
    assert reads == []


def test_without_live_opt_in_no_network_no_source_url_no_secret(pilot, capsys):
    reads, _ = pilot
    assert main(args(PYTHON, live=False)) == EXIT_REFUSED
    captured = capsys.readouterr()
    assert captured.out == ""
    assert TOKEN not in captured.err and PYTHON not in captured.err
    assert reads == []


def test_two_source_off_allowlist_preflight_refuses_without_fetch(pilot, capsys):
    reads, _ = pilot
    assert main(args(PYTHON, UNAPPROVED)) == EXIT_REFUSED
    cap = capsys.readouterr()
    assert cap.out == ""
    assert UNAPPROVED not in cap.err and TOKEN not in cap.err
    assert reads == []


@pytest.mark.parametrize("sources", [
    (PYTHON, PYTHON),
    (PYTHON, "https://www.python.org/another"),
    (PYTHON, IANA, UNAPPROVED),
    (PYTHON, "http://www.iana.org/domains/reserved"),
    (PYTHON, "https://127.0.0.1/private"),
])
def test_duplicate_host_or_unsafe_or_excess_source_refused_before_network(pilot, sources):
    reads, _ = pilot
    status, result = run(args(*sources))
    assert status == EXIT_REFUSED and result is None
    assert reads == []


@pytest.mark.parametrize("max_age", ["-1", "inf", "nan", "0"])
def test_invalid_staleness_window_refused_before_network(pilot, max_age):
    reads, _ = pilot
    status, report = run(args(PYTHON, age=max_age))
    assert status == EXIT_REFUSED and report is None
    assert reads == []


def test_missing_operator_token_in_pilot_does_not_fetch(pilot, monkeypatch):
    reads, _ = pilot
    monkeypatch.delenv("ARL_PILOT_BEARER_TOKEN")
    assert run(args(PYTHON)) == (EXIT_REFUSED, None)
    assert reads == []


def test_development_mode_cannot_disguise_pilot(pilot, monkeypatch):
    reads, _ = pilot
    monkeypatch.setenv("ARL_RUNTIME_MODE", "development")
    assert run(args(PYTHON)) == (EXIT_REFUSED, None)
    assert reads == []


@pytest.mark.parametrize("mode", ["single", "pair"])
def test_stale_capture_abstains_with_no_source_metadata(pilot, mode):
    reads, records = pilot
    when = datetime.now(timezone.utc)-timedelta(hours=3)
    records[IANA if mode == "pair" else PYTHON] = capture(
        IANA if mode == "pair" else PYTHON, observed=when,
    )
    status, report = run(args(PYTHON, IANA) if mode=="pair" else args(PYTHON))
    assert status == EXIT_ABSTAIN
    assert report["citations"] == []
    assert report["decision"] == "abstain"
    assert report["may_use_as_bounded_evidence"] is False
    assert reads in ([PYTHON], [PYTHON, IANA])


def test_reader_network_exception_cannot_echo_secret_or_original_text(pilot, capsys):
    reads, records = pilot
    records[PYTHON] = RuntimeError("private-token="+TOKEN+" injected "+POSITIVE)
    code = main(args(PYTHON, quotes=True))
    stdout, stderr = capsys.readouterr()
    assert code == EXIT_ABSTAIN
    report = json.loads(stdout)
    assert report["citations"] == []
    assert TOKEN not in stdout + stderr
    assert POSITIVE not in stdout + stderr
    assert reads == [PYTHON]


def test_success_json_is_one_line_and_never_exposes_credentials(pilot, capsys):
    reads, _ = pilot
    assert main(args(PYTHON, IANA)) == EXIT_BOUNDED
    outputs = capsys.readouterr()
    assert outputs.err == ""
    assert len(outputs.out.splitlines()) == 1
    assert TOKEN not in outputs.out
    assert len(json.loads(outputs.out)["citations"]) == 2


def test_source_url_is_not_disclosed_on_abstention(pilot):
    reads, records = pilot
    records[IANA] = capture(IANA, "Information on IANA example domains.")
    status, result = run(args(PYTHON, IANA, quotes=True))
    assert status == EXIT_ABSTAIN
    assert result["citations"] == []
    assert PYTHON not in json.dumps(result)
    assert IANA not in json.dumps(result)
    assert POSITIVE not in json.dumps(result)
    assert reads == [PYTHON, IANA]
