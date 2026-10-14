"""Step 245: local, explicit source-verified claim check for app developers.

No external API hosting, unrestricted source discovery, model inference or
autonomous action. Network is forbidden unless --live AND pilot config with
approved exact HTTPS source URLs. Credentials come only from environment;
neither source exceptions nor token contents appear in results.
"""
from __future__ import annotations

import argparse
import json
import os
import sys

from fastapi.testclient import TestClient
from pydantic import ValidationError

from backend.app.api.original_source_claim import OriginalSourceClaimRequest
from backend.app.api.two_origin_answer import TwoOriginAnswerRequest
from backend.app.api.pilot_auth import pilot_runtime_configuration
from backend.app.integrations.cited_answer_client import check_cited_answer_with_api
from backend.app.integrations.two_origin_answer_client import check_two_origin_answer_with_api
from backend.app.main import app
from backend.app.orchestrator.dependencies import OrchestrationDependencies
from backend.app.reality.allowlisted_https_source_reader import AllowlistedHttpsSourceReader

# Distinguish a completed bounded observation from a conservative abstention.
EXIT_BOUNDED = 0
EXIT_ABSTAIN = 2
EXIT_REFUSED = 3
EXIT_INTERNAL = 4


class _Refused(ValueError):
    """Only generic explanations are printed; no credentials or source text."""


def _parse(argv: list[str] | None):
    parser = argparse.ArgumentParser(
        description="Locally verify 1 or 2 operator-allowlisted original HTTPS sources.",
        add_help=True,
    )
    parser.add_argument("--claim", required=True, help="Narrow atomic claim sentence.")
    parser.add_argument("--entity", required=True, help="Exact subject of the claim.")
    parser.add_argument(
        "--source", action="append", required=True, dest="sources",
        help="Exact operator-allowlisted HTTPS page; repeat once for comparison.",
    )
    parser.add_argument(
        "--max-age", type=float, default=3600.0, dest="age",
        help="Maximum age in seconds of observed source, default 3600.",
    )
    parser.add_argument(
        "--live", action="store_true",
        help="Explicit consent to perform original-source HTTPS reads.",
    )
    parser.add_argument(
        "--include-untrusted-quotes", action="store_true",
        help="Include raw publisher statements in JSON as UNTRUSTED data.",
    )
    return parser.parse_args(argv)


def _build_request(options):
    if len(options.sources) == 1:
        return OriginalSourceClaimRequest(
            claim_text=options.claim, entity=options.entity,
            source_uri=options.sources[0],
            freshness_max_age_seconds=options.age,
        )
    if len(options.sources) == 2:
        return TwoOriginAnswerRequest(
            claim_text=options.claim, entity=options.entity,
            source_uris=options.sources,
            freshness_max_age_seconds=options.age,
        )
    raise _Refused("only 1 or 2 approved sources can be checked")


def _prepare_operator(request):
    # No network if the operator has not explicitly configured strict pilot
    # access, regardless of whether the local TestClient is trusted.
    enabled, _ = pilot_runtime_configuration()
    token = os.environ.get("ARL_PILOT_BEARER_TOKEN")
    if enabled is not True or token is None:
        raise _Refused("pilot access is required")
    reader = OrchestrationDependencies.default().independent_source_text_assurance._reader
    if not isinstance(reader, AllowlistedHttpsSourceReader):
        raise _Refused("operator source reader not installed")
    urls = (
        (request.source_uri,)
        if isinstance(request, OriginalSourceClaimRequest)
        else tuple(request.source_uris)
    )
    if any(uri not in reader._allowed for uri in urls):
        raise _Refused("requested source is not operator approved")
    return token


def _render_result(result, *, include_quotes: bool, paired: bool) -> dict:
    citations = result.citations if paired else (
        (result.citation,) if result.citation is not None else ()
    )
    rows = []
    for citation in citations:
        row = {
            "source_uri": citation.source_uri,
            "source_quote_sha256": citation.source_quote_sha256,
            "source_capture_sha256": citation.source_capture_sha256,
            "source_capture_observed_at": citation.source_capture_observed_at,
        }
        if include_quotes:
            row["untrusted_original_source_quote"] = citation.original_source_quote
        rows.append(row)
    # These explicit false epistemic flags are required, never inferred from
    # a single aligned source or two hostnames.
    response = {
        "scope": "bounded_original_source_observations",
        "decision": result.decision,
        "answer_text": result.answer_text,
        "reason_code": result.reason_code,
        "request_binding_sha256": result.request_binding_sha256,
        "may_use_as_bounded_evidence": result.may_use_as_bounded_evidence,
        "citations": rows,
        "factual_truth_verified": False,
        "publisher_authorship_verified": False,
        "independently_owned_publishers_verified": False,
        "general_question_answering": False,
        "neural_model_used": False,
    }
    if paired:
        response["distinct_https_hostnames"] = result.distinct_https_hostnames
    return response


def run(argv: list[str] | None = None) -> tuple[int, dict | None]:
    """Return safe machine-readable report without ever printing a secret.

    Caller decides whether to render JSON. Syntax/preflight/network failures
    are bounded to an exit code; no exception string from transport surfaces.
    """
    try:
        args = _parse(argv)
        if not args.live:
            return EXIT_REFUSED, None
        request = _build_request(args)
        token = _prepare_operator(request)
        with TestClient(app) as http:
            if isinstance(request, TwoOriginAnswerRequest):
                result = check_two_origin_answer_with_api(http, token, request)
                paired = True
            else:
                result = check_cited_answer_with_api(http, token, request)
                paired = False
        report = _render_result(
            result, include_quotes=args.include_untrusted_quotes, paired=paired,
        )
        return (EXIT_ABSTAIN if result.decision == "abstain" else EXIT_BOUNDED), report
    except (ValueError, TypeError, ValidationError, _Refused):
        return EXIT_REFUSED, None
    except Exception:
        return EXIT_INTERNAL, None


def main(argv: list[str] | None = None) -> int:
    try:
        status, report = run(argv)
    except SystemExit:
        # argparse's parse/help behavior is allowed when explicitly launched.
        raise
    if report is not None:
        print(json.dumps(report, sort_keys=True, ensure_ascii=True))
    elif status == EXIT_REFUSED:
        print("Original-source check refused: invalid or unauthorized configuration.", file=sys.stderr)
    else:
        print("Original-source check unavailable; no evidence returned.", file=sys.stderr)
    return status


if __name__ == "__main__":
    raise SystemExit(main())
