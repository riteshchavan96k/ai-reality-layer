"""Live Step 227 fixed original-publisher atomic assertion smoke.

Opt-in only. No user URL, no arbitrary text, no HTML/credentials in output.
This verifies bounded source-backed assertion interpretation, not factual truth.
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from fastapi.testclient import TestClient

from backend.app.main import app
from backend.app.orchestrator.dependencies import OrchestrationDependencies
from backend.app.reality.allowlisted_https_source_reader import AllowlistedHttpsSourceReader
from backend.app.evaluation.live_source_quality_smoke import (
    PUBLISHER_URL, EXPECTED_EXCERPT, _checked_capture,
)

GOOD_CLAIM = "Python 3.13.0 is a stable release."
BAD_CLAIM = "Python 3.13.0 is not a stable release."


def run_live_smoke() -> dict:
    deps = OrchestrationDependencies.default()
    reader = deps.independent_source_text_assurance._reader
    if (
        not isinstance(reader, AllowlistedHttpsSourceReader)
        or reader._allowed != frozenset({PUBLISHER_URL})
    ):
        raise ValueError("exact_operator_allowlist_required")

    # Genuine socket/TLS/HTTPS, original independently declared source anchors.
    capture = _checked_capture(reader(PUBLISHER_URL))
    with TestClient(app) as client:
        results = []
        for key, claim, expected_state, expected_alignment in (
            ("stable_release", GOOD_CLAIM, "supported", "aligned"),
            ("negated_stable_release", BAD_CLAIM, "uncertain", "contradicted"),
        ):
            response = client.post("/api/v1/reality-state/evidence", json={
                "task": "Does the original publisher call Python 3.13.0 stable?",
                "entity": "Python 3.13.0",
                "documents": [{"uri": PUBLISHER_URL, "content": EXPECTED_EXCERPT}],
                "freshness_max_age_seconds": 3600,
                "require_independent_source_text_match": True,
                "require_claim_alignment": True,
                "claim_text": claim,
            })
            if response.status_code != 200:
                raise ValueError("strict_api_unavailable")
            state = response.json()
            assurance = state.get("evidence", {}).get("independent_source_text_assurance", {})
            alignment = state.get("evidence", {}).get("claim_alignment", {})
            audit = assurance.get("sources", [])
            observed = state.get("source_observation", {}).get("observations", [])
            if (
                state.get("status") != expected_state
                or assurance.get("status") != "exact_text_observed"
                or alignment.get("status") != expected_alignment
                or alignment.get("semantic_support_verified") is not False
                or alignment.get("factual_truth_verified") is not False
                or not isinstance(audit, list) or len(audit) != 1
                or audit[0].get("source_ref") != PUBLISHER_URL
                or audit[0].get("assertion_context_status") != "unique_standalone_unit"
                or not audit[0].get("capture_sha256")
                or not audit[0].get("capture_observed_at")
                or not isinstance(observed, list) or len(observed) != 1
                or observed[0].get("observation_method") != "independent_source_capture"
                or observed[0].get("observed_at") != audit[0]["capture_observed_at"]
            ):
                raise ValueError("claim_alignment_live_oracle_mismatch")
            results.append({
                "scenario_id": key,
                "state": state["status"],
                "claim_alignment": alignment["status"],
            })
    return {
        "dataset_id": "step227-one-original-publisher-atomic-claim-v1",
        "corpus_type": "two_fixed_source-backed_assertion_cases",
        "publisher_url": PUBLISHER_URL,
        "capture": capture,
        "scenario_count": 2,
        "cases": results,
        "semantic_support_verified": False,
        "factual_truth_verified": False,
        "population_factual_accuracy_established": False,
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--live", action="store_true")
    parser.add_argument("--output", type=Path)
    args = parser.parse_args(argv)
    if not args.live:
        parser.error("network disabled by default; --live required")
    try:
        result = run_live_smoke()
        data = json.dumps(result, sort_keys=True, indent=2) + "\n"
        if args.output:
            args.output.write_text(data, encoding="utf-8")
        print(data, end="")
        return 0
    except Exception:
        # Never print provider exception messages, user text or publisher body.
        print("Step 227 live canary unavailable or policy mismatch")
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
