"""Step 232: versioned, developer-labeled *live original-source* policy evaluation.

Run with --live only. Fixed original publisher URLs, fixed source excerpts and
claims, no user-controlled fetch destinations or arbitrary prompts.
This measures conservative policy outcomes on twelve predeclared examples,
not population accuracy, independent human labels or factual truth.
"""

from __future__ import annotations

import argparse
from datetime import datetime, timezone
from hashlib import sha256
import json
import os
from pathlib import Path
import re
from typing import Any

from fastapi.testclient import TestClient

from backend.app.main import app
from backend.app.orchestrator.dependencies import OrchestrationDependencies
from backend.app.reality.allowlisted_https_source_reader import AllowlistedHttpsSourceReader
from backend.app.evaluation.multi_publisher_live_smoke import PUBLISHERS, _check_receipt

DATASET = (
    Path(__file__).resolve().parents[2]
    / "evaluation_fixtures" / "step232_original_source_claim_v1.json"
)
DATASET_ID = "step232-fixed-original-source-claim-policy-v1"
SOURCES = {
    "python313": "https://www.python.org/downloads/release/python-3130/",
    "ianareserved": "https://www.iana.org/domains/reserved",
}
EXPECTED_CASE_COUNT = 12
RELATIONS = frozenset({
    "supports_claim", "contradicts_claim", "unrelated_claim",
    "ambiguous_or_hedged", "forged_evidence", "incomplete_excerpt",
    "needs_semantic_context",
})
EXPECTED_CASE_IDS = frozenset({
    "python-direct-supported", "python-supported-but-outside-grammar",
    "python-direct-negation", "python-unrelated-entity",
    "python-different-property", "python-hedged-claim",
    "python-forged-release-date", "python-partial-unit",
    "iana-genuine-but-semantically-unsupported",
    "iana-forged-registration", "iana-genuine-unrelated",
    "iana-python-text-misattribution",
})
DIGEST = re.compile(r"[a-f0-9]{64}")


class Step232GateError(ValueError):
    """Fixed, nonsecret policy failure, safe to write to CI logs."""


def load_dataset(path: Path = DATASET) -> dict[str, Any]:
    raw = json.loads(Path(path).read_text(encoding="utf-8"))
    if (
        not isinstance(raw, dict)
        or raw.get("dataset_id") != DATASET_ID
        or raw.get("schema_version") != "1.0"
        or raw.get("label_provenance")
        != "developer-authored-before-new_live_capture_not_independent_human_review"
        or raw.get("representative_population") is not False
    ):
        raise Step232GateError("dataset_provenance_invalid")
    sources, cases = raw.get("sources"), raw.get("cases")
    if (
        not isinstance(sources, list)
        or len(sources) != 2
        or any(
            not isinstance(s, dict)
            or s.get("id") not in SOURCES
            or s.get("url") != SOURCES[s.get("id")]
            or not isinstance(s.get("anchor"), str)
            or not (1 <= len(s["anchor"]) <= 200)
            for s in sources
        )
        or {s["id"] for s in sources} != set(SOURCES)
    ):
        raise Step232GateError("fixed_original_source_set_invalid")
    if not isinstance(cases, list) or len(cases) != EXPECTED_CASE_COUNT:
        raise Step232GateError("case_count_changed_requires_new_version")
    ids = set()
    positive_count = 0
    for case in cases:
        if not isinstance(case, dict):
            raise Step232GateError("invalid_case_schema")
        case_id = case.get("id")
        if (
            not isinstance(case_id, str)
            or case_id not in EXPECTED_CASE_IDS
            or case_id in ids
            or case.get("source_id") not in SOURCES
            or case.get("reference_relation") not in RELATIONS
            or case.get("expected_decision") not in {"supported", "abstain"}
            or case.get("expected_alignment") not in
            {"aligned", "contradicted", "insufficient", "conflicting"}
        ):
            raise Step232GateError("invalid_case_labels")
        ids.add(case_id)
        for field in ("excerpt", "claim"):
            item = case.get(field)
            if (
                not isinstance(item, str)
                or not item.strip()
                or len(item) > 500
                or "\r" in item
                or "\n" in item
            ):
                raise Step232GateError("invalid_case_text")
        relation = case["reference_relation"]
        if case["expected_decision"] == "supported":
            if relation != "supports_claim" or case["expected_alignment"] != "aligned":
                raise Step232GateError("invalid_positive_label")
        elif case["expected_alignment"] == "aligned":
            raise Step232GateError("unexpected_alignment_in_abstention")
        if relation == "supports_claim":
            positive_count += 1
    if ids != EXPECTED_CASE_IDS or positive_count != 2:
        raise Step232GateError("case_identity_or_positive_count_mismatch")
    return raw


def judge_case(case: dict[str, Any], response: dict[str, Any]) -> dict[str, Any]:
    """Strictly check one *actual API* response, never score its input label as output."""
    if not isinstance(response, dict):
        raise Step232GateError("malformed_api_response")
    alignment = response.get("evidence", {}).get("claim_alignment", {})
    assurance = response.get("evidence", {}).get("independent_source_text_assurance", {})
    state = response.get("status")
    alignment_status = alignment.get("status")
    if (
        state not in {"supported", "uncertain", "insufficient", "unavailable"}
        or alignment_status != case["expected_alignment"]
        or alignment.get("factual_truth_verified") is not False
        or alignment.get("semantic_support_verified") is not False
        or assurance.get("publisher_authenticated") is not False
        or assurance.get("semantic_support_verified") is not False
        or alignment.get("source_count") != 1
    ):
        raise Step232GateError("unexpected_source_claim_alignment_or_authority")
    decisions = alignment.get("source_decisions")
    if (
        not isinstance(decisions, list)
        or len(decisions) != 1
        or decisions[0].get("source_ref") != SOURCES[case["source_id"]]
        or decisions[0].get("relationship") != alignment_status
    ):
        raise Step232GateError("source_scoped_claim_decision_invalid")
    rows = assurance.get("sources")
    if (
        not isinstance(rows, list) or len(rows) != 1
        or rows[0].get("source_ref") != SOURCES[case["source_id"]]
    ):
        raise Step232GateError("source_audit_identity_invalid")
    row = rows[0]
    if alignment_status in {"aligned", "contradicted"}:
        if (
            row.get("status") != "exact_text_observed"
            or row.get("assertion_context_status") != "unique_standalone_unit"
            or row.get("source_quote_context_status") != "no_matching_html_quote_unit"
            or not isinstance(row.get("capture_sha256"), str)
            or DIGEST.fullmatch(row["capture_sha256"]) is None
            or not isinstance(row.get("capture_observed_at"), str)
            or not row["capture_observed_at"].endswith("Z")
        ):
            raise Step232GateError("missing_real_source_capture_audit")
    should_support = case["expected_decision"] == "supported"
    if (state == "supported") != should_support:
        raise Step232GateError("false_support_or_missing_supported_case")
    # Do not serialize user/publisher text, token, raw HTML or network errors.
    return {
        "id": case["id"],
        "source_id": case["source_id"],
        "reference_relation": case["reference_relation"],
        "expected_decision": case["expected_decision"],
        "state": state,
        "alignment": alignment_status,
    }


def summarize(cases: list[dict[str, Any]], observations: list[dict[str, Any]]) -> dict[str, Any]:
    if len(observations) != len(cases):
        raise Step232GateError("evaluation_incomplete")
    positive_ids = {x["id"] for x in cases if x["reference_relation"] == "supports_claim"}
    supported = {x["id"] for x in observations if x["state"] == "supported"}
    if not supported <= positive_ids:
        raise Step232GateError("false_support_in_benchmark")
    correct_policy_count = sum(
        (x["state"] == "supported") == (x["expected_decision"] == "supported")
        for x in observations
    )
    if correct_policy_count != len(cases):
        raise Step232GateError("policy_mismatch")
    return {
        "dataset_id": DATASET_ID,
        "review_status": "developer_labeled_NOT_independently_human_reviewed",
        "corpus_type": "fixed_original_publisher_HTTPS_policy_challenge_not_population_sample",
        "publisher_count": len(SOURCES),
        "scenario_count": len(cases),
        "reference_positive_count": len(positive_ids),
        "reference_positive_supported": len(supported),
        "reference_positive_abstained": len(positive_ids - supported),
        "reference_nonpositive_count": len(cases) - len(positive_ids),
        "reference_nonpositive_falsely_supported": 0,
        "policy_conformant_count": correct_policy_count,
        "publisher_authenticated": False,
        "semantic_support_verified": False,
        "factual_truth_verified": False,
        "population_factual_accuracy_established": False,
        "external_deployment_verified": False,
        "cases": observations,
    }


def run_live() -> dict[str, Any]:
    if os.environ.get("ARL_RUNTIME_MODE", "development") != "development":
        raise Step232GateError("offline_ci_development_mode_required")
    dataset = load_dataset()
    deps = OrchestrationDependencies.default()
    reader = deps.independent_source_text_assurance._reader
    if not isinstance(reader, AllowlistedHttpsSourceReader):
        raise Step232GateError("genuine_https_reader_not_configured")
    if reader._allowed != frozenset(SOURCES.values()):
        raise Step232GateError("exact_two_url_allowlist_required")
    receipts = {}
    for source in dataset["sources"]:
        # Same independently executed direct HTTPS reader as the real API.
        # The capture contains real wire-body digest and server UTC timestamp.
        receipts[source["id"]] = _check_receipt(
            {"id": source["id"], "url": source["url"], "anchors": (source["anchor"],)},
            reader(source["url"]),
        )

    observations = []
    with TestClient(app) as client:
        for case in dataset["cases"]:
            source_id = case["source_id"]
            res = client.post("/api/v1/reality-state/evidence", json={
                "task": "Assess bounded claim against server-observed original source",
                "entity": "Python 3.13.0" if source_id == "python313" else "example.com",
                "documents": [{"uri": SOURCES[source_id], "content": case["excerpt"]}],
                "freshness_max_age_seconds": 3600,
                "require_independent_source_text_match": True,
                "require_claim_alignment": True,
                "claim_text": case["claim"],
            })
            if res.status_code != 200:
                raise Step232GateError("live_reality_state_api_non_200")
            observations.append(judge_case(case, res.json()))
    result = summarize(dataset["cases"], observations)
    # No raw page content, quotes, request bodies, URLs or secrets in report.
    result["capture_receipts"] = receipts
    return result


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--live", action="store_true")
    parser.add_argument("--output", type=Path)
    args = parser.parse_args(argv)
    if not args.live:
        parser.error("live network is disabled by default; --live required")
    try:
        result = run_live()
        output = json.dumps(result, sort_keys=True, indent=2) + "\n"
        if args.output:
            args.output.write_text(output, encoding="utf-8")
        print(output, end="")
        return 0
    except Step232GateError as exc:
        print("Step 232 gated source policy evaluation failed: " + str(exc))
        return 1
    except Exception:
        # Never print arbitrary source body, transport errors or credentials.
        print("Step 232 gated source policy evaluation failed: reader_or_api_unavailable")
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
