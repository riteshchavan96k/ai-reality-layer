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
from backend.app.integrations.source_recheck import recheck_cited_answer_with_api
from backend.app.integrations.source_history import (
    InvalidHistory, operator_history_configuration,
    save_verified_answer, load_verified_answer,
)
from backend.app.integrations.source_timeline import (
    latest_timeline_answer, append_verified_recheck, inspect_timeline,
)
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
    history_modes = parser.add_mutually_exclusive_group()
    history_modes.add_argument(
        "--recheck", action="store_true",
        help="Capture the same approved source twice in this single invocation.",
    )
    history_modes.add_argument(
        "--save-observation", action="store_true",
        help="Save one validated observation to a private, keyed local history.",
    )
    history_modes.add_argument(
        "--recheck-record", metavar="RECORD_ID",
        help="Recheck one MAC-verified observation saved in an earlier invocation.",
    )
    history_modes.add_argument(
        "--timeline-append", metavar="ROOT_RECORD_ID",
        help="Explicitly recheck the latest record of a validated timeline and append it atomically.",
    )
    history_modes.add_argument(
        "--timeline-show", metavar="ROOT_RECORD_ID",
        help="Read a local, bounded, MAC-verified timeline; does not perform HTTPS requests.",
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


def _render_recheck(result, *, include_quotes: bool) -> dict:
    # Both observations must be validated; never reveal one partial receipt.
    output = {
        "scope": "two_observations_of_one_original_source",
        "recheck_status": result.status,
        "answer_text": result.answer_text,
        "request_binding_sha256": result.request_binding_sha256,
        "previous_decision": result.previous_decision,
        "current_decision": result.current_decision,
        "may_use_as_bounded_evidence": result.may_use_current_as_bounded_evidence,
        "observations": [],
        "historical_receipt_authenticated": False,
        "factual_truth_verified": False,
        "publisher_authorship_verified": False,
        "independently_owned_publishers_verified": False,
        "general_question_answering": False,
        "automatic_monitoring_enabled": False,
    }
    if result.status == "abstain" or result.previous is None or result.current is None:
        return output
    for role, citation in (("previous", result.previous), ("current", result.current)):
        item = {
            "role": role,
            "source_uri": citation.source_uri,
            "source_quote_sha256": citation.source_quote_sha256,
            "source_capture_sha256": citation.source_capture_sha256,
            "source_capture_observed_at": citation.source_capture_observed_at,
        }
        if include_quotes:
            item["untrusted_original_source_quote"] = citation.original_source_quote
        output["observations"].append(item)
    return output


def run(argv: list[str] | None = None) -> tuple[int, dict | None]:
    """Return safe machine-readable report without ever printing a secret.

    Caller decides whether to render JSON. Syntax/preflight/network failures
    are bounded to an exit code; no exception string from transport surfaces.
    """
    try:
        args = _parse(argv)
        if not args.live and args.timeline_show is None:
            return EXIT_REFUSED, None
        request = _build_request(args)
        if (
            args.recheck or args.save_observation or args.recheck_record is not None
            or args.timeline_append is not None or args.timeline_show is not None
        ) and not isinstance(request, OriginalSourceClaimRequest):
            raise _Refused("source history supports exactly one approved source")
        token = _prepare_operator(request)
        history = None
        if (
            args.save_observation or args.recheck_record is not None
            or args.timeline_append is not None or args.timeline_show is not None
        ):
            # Check local permissions/key before a fresh publisher request.
            try:
                history = operator_history_configuration()
            except InvalidHistory:
                return EXIT_REFUSED, None
        if args.timeline_show is not None:
            try:
                return EXIT_BOUNDED, inspect_timeline(*history, args.timeline_show, request)
            except InvalidHistory:
                return EXIT_ABSTAIN, None
        # Verify the *complete* existing chain before authorizing fresh HTTPS.
        timeline_preflight = None
        if args.timeline_append is not None:
            try:
                timeline_preflight = latest_timeline_answer(
                    *history, args.timeline_append, request,
                )
            except InvalidHistory:
                return EXIT_ABSTAIN, None
        with TestClient(app) as http:
            if args.timeline_append is not None:
                expected_latest, latest = timeline_preflight
                comparison = recheck_cited_answer_with_api(http, token, request, latest)
                if comparison.status == "abstain":
                    return EXIT_ABSTAIN, _render_recheck(comparison, include_quotes=False)
                try:
                    new_id, length = append_verified_recheck(
                        *history, args.timeline_append, request,
                        expected_latest, comparison,
                    )
                except InvalidHistory:
                    return EXIT_ABSTAIN, None
                report = _render_recheck(
                    comparison, include_quotes=args.include_untrusted_quotes,
                )
                report["timeline_root_id"] = args.timeline_append
                report["appended_record_id"] = new_id
                report["timeline_observation_count"] = length
                return EXIT_BOUNDED, report
            if args.recheck_record is not None:
                try:
                    earlier = load_verified_answer(*history, args.recheck_record, request)
                except InvalidHistory:
                    return EXIT_ABSTAIN, None
                comparison = recheck_cited_answer_with_api(
                    http, token, request, earlier,
                )
                return (
                    EXIT_ABSTAIN if comparison.status == "abstain" else EXIT_BOUNDED,
                    _render_recheck(comparison, include_quotes=args.include_untrusted_quotes),
                )
            if args.save_observation:
                observed = check_cited_answer_with_api(http, token, request)
                report = _render_result(
                    observed, include_quotes=args.include_untrusted_quotes, paired=False,
                )
                if observed.decision == "abstain":
                    return EXIT_ABSTAIN, report
                try:
                    record_id = save_verified_answer(*history, request, observed)
                except InvalidHistory:
                    return EXIT_ABSTAIN, None
                report["saved_record_id"] = record_id
                report["historical_receipt_authenticated"] = False
                return EXIT_BOUNDED, report
            if args.recheck:
                previous = check_cited_answer_with_api(http, token, request)
                rechecked = recheck_cited_answer_with_api(
                    http, token, request, previous,
                )
                report = _render_recheck(
                    rechecked, include_quotes=args.include_untrusted_quotes,
                )
                return (
                    EXIT_ABSTAIN if rechecked.status == "abstain" else EXIT_BOUNDED,
                    report,
                )
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
