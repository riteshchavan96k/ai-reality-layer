"""Step 233 real TLS claim-reason safety smoke.

Uses the predeclared Step 232 two-official-publisher source cases and its
actual strict FastAPI API+original HTTPS reader. No network unless --live.
The fixture remains unchanged; this is an additional independent reason oracle.
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from backend.app.evaluation.step232_source_claim_safety import run_live

EXPECTED_REASON_CODES = {
    "python-direct-supported": "bounded_assertion_aligned",
    "python-supported-but-outside-grammar": "source_grammar_unsupported",
    "python-direct-negation": "bounded_assertion_contradicted",
    "python-unrelated-entity": "atomic_relationship_undetermined",
    "python-different-property": "atomic_relationship_undetermined",
    "python-hedged-claim": "claim_grammar_unsupported",
    "python-forged-release-date": "independent_source_unverified",
    "python-partial-unit": "independent_source_unverified",
    "iana-genuine-but-semantically-unsupported": "source_grammar_unsupported",
    "iana-forged-registration": "independent_source_unverified",
    "iana-genuine-unrelated": "source_grammar_unsupported",
    "iana-python-text-misattribution": "independent_source_unverified",
}


def run_reason_smoke() -> dict:
    live = run_live()  # Runs actual real-source TLS and API calls, no fake provider.
    rows = live.get("cases")
    if not isinstance(rows, list) or len(rows) != len(EXPECTED_REASON_CODES):
        raise ValueError("live_reason_case_count_mismatch")
    seen = set()
    safe_rows = []
    for row in rows:
        name = row.get("id") if isinstance(row, dict) else None
        if (
            name not in EXPECTED_REASON_CODES
            or name in seen
            or row.get("reason_code") != EXPECTED_REASON_CODES[name]
        ):
            raise ValueError("unexpected_source_claim_reason")
        seen.add(name)
        safe_rows.append({
            "scenario_id": name,
            "alignment": row["alignment"],
            "reason_code": row["reason_code"],
            "supported": row["state"] == "supported",
        })
    if seen != set(EXPECTED_REASON_CODES):
        raise ValueError("source_reason_case_set_mismatch")
    receipts = live.get("capture_receipts")
    if not isinstance(receipts, dict) or set(receipts) != {"python313", "ianareserved"}:
        raise ValueError("source_receipts_missing")
    # Step232 already validated digest + server observation time. No
    # publisher HTML, arbitrary requests or secret-bearing URLs are emitted.
    return {
        "dataset_id": "step233-original-source-decision-reasons-v1",
        "audit_type": "developer_predeclared_fixed_live_policy_not_field_accuracy",
        "reason_case_count": len(rows),
        "reason_correct_count": len(safe_rows),
        "known_positive_safe_abstention": "source_grammar_unsupported",
        "false_supported_nonpositive": live["reference_nonpositive_falsely_supported"],
        "source_capture_receipts": receipts,
        "cases": safe_rows,
        "independently_human_labeled": False,
        "population_factual_accuracy_established": False,
        "general_semantic_entailment": False,
        "deployed_publicly": False,
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--live", action="store_true")
    parser.add_argument("--output", type=Path)
    args = parser.parse_args(argv)
    if not args.live:
        parser.error("network disabled by default; explicit --live required")
    try:
        report = run_reason_smoke()
        text = json.dumps(report, sort_keys=True, indent=2) + "\n"
        if args.output:
            args.output.write_text(text, encoding="utf-8")
        print(text, end="")
        return 0
    except Exception:
        # Never expose transport exception, source body, or source credentials.
        print("Step 233 real-source explanation audit failed")
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
