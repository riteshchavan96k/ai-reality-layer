"""Step 217: reproducible, oracle-labeled Reality State quality baseline.

This benchmark does NOT certify factual truth: the fixed offline corpus uses
clearly labeled hypothetical sources and an independent *simulated* oracle.
No ML, network access, source authentication, or product confidence changes.
"""

from __future__ import annotations

import argparse
from collections import Counter
from dataclasses import replace
from datetime import datetime
import json
from pathlib import Path
from typing import Any

from backend.app.api.evidence_reality_state import EvidenceRealityStateRequest
from backend.app.api.reality_state import RealityStateResponse
from backend.app.orchestrator.dependencies import OrchestrationDependencies
from backend.app.orchestrator.orchestrator import build_reality_state_from_evidence
from backend.app.reality.reality_state_builder import RealityStateBuilder
from backend.app.reality.source_freshness_evaluator import SourceFreshnessEvaluator


DATASET_PATH = (
    Path(__file__).resolve().parents[2]
    / "evaluation_fixtures"
    / "step217_controlled_v1.json"
)
SCENARIOS = frozenset(
    {
        "verified_consistent",
        "unverified_false_source",
        "explicit_negation",
        "outdated_report",
        "paraphrased_disagreement",
        "missing_freshness_policy",
    }
)
# Evaluation target is explicit and deliberately limited to this offline corpus.
DATASET_VERSION = "step217-controlled-v1"


def _claim_key(text: str) -> str:
    return " ".join(text.split()).casefold()


def _pair_key(a: str, b: str) -> tuple[str, str]:
    return tuple(sorted((_claim_key(a), _claim_key(b))))


def _ratio(numerator: int, denominator: int) -> float | None:
    return numerator / denominator if denominator else None


def _f1(precision: float | None, recall: float | None) -> float | None:
    if precision is None or recall is None:
        return None
    return 2 * precision * recall / (precision + recall) if precision + recall else 0.0


def _require(check: bool, message: str) -> None:
    if not check:
        raise ValueError("invalid Step 217 dataset: " + message)


def load_dataset(path: Path = DATASET_PATH) -> dict[str, Any]:
    """Validate fixed labels separately from the Reality State input path."""
    raw = json.loads(Path(path).read_text(encoding="utf-8"))
    _require(isinstance(raw, dict), "root must be a mapping")
    _require(raw.get("dataset_id") == DATASET_VERSION, "unexpected dataset_id")
    _require(raw.get("schema_version") == "1.0", "unexpected schema version")
    _require("controlled" in str(raw.get("provenance", "")).lower(), "fixture provenance missing")
    _require(isinstance(raw.get("cases"), list) and len(raw["cases"]) >= 40, "requires at least 40 cases")
    instant = datetime.fromisoformat(raw["evaluation_clock_utc"].replace("Z", "+00:00"))
    _require(instant.tzinfo is not None, "clock must be timezone-aware")
    seen_ids: set[str] = set()
    seen_scenarios: Counter[str] = Counter()
    for case in raw["cases"]:
        _require(isinstance(case, dict), "case must be a mapping")
        case_id = case.get("id")
        _require(isinstance(case_id, str) and case_id and case_id not in seen_ids, "unique case id required")
        seen_ids.add(case_id)
        scenario = case.get("scenario")
        _require(scenario in SCENARIOS, f"{case_id}: unknown scenario")
        seen_scenarios[scenario] += 1
        gold = case.get("gold")
        _require(isinstance(gold, dict), f"{case_id}: missing gold")
        _require(gold.get("world_reference_is_simulated") is True, f"{case_id}: oracle must declare simulation")
        _require(type(gold.get("should_abstain")) is bool, f"{case_id}: missing independent abstention label")
        _require(isinstance(gold.get("justification"), str) and gold["justification"].strip(), f"{case_id}: missing justification")
        _require(isinstance(gold.get("world_reference_claim"), str), f"{case_id}: missing oracle claim")
        raw_claims = gold.get("expected_claims")
        _require(isinstance(raw_claims, list) and raw_claims, f"{case_id}: no claim labels")
        _require(isinstance(gold.get("expected_conflict_pairs"), list), f"{case_id}: invalid conflict pairs")
        documents = case.get("documents")
        _require(isinstance(documents, list) and documents, f"{case_id}: no documents")
        _require(len({d["uri"] for d in documents}) == len(documents), f"{case_id}: duplicate document URIs")
        _require(all(d["uri"].startswith("https://fixtures.example.test/") for d in documents), f"{case_id}: must use clearly fictional fixture URIs")
        doc_refs = {doc["uri"] for doc in documents}
        gold_claim_ids: set[str] = set()
        for label in raw_claims:
            _require(isinstance(label, dict) and isinstance(label.get("text"), str), f"{case_id}: invalid claim label")
            key = _claim_key(label["text"])
            _require(key not in gold_claim_ids, f"{case_id}: repeated gold claim")
            gold_claim_ids.add(key)
            refs = label.get("source_refs")
            _require(isinstance(refs, list) and refs and set(refs) <= doc_refs and len(set(refs)) == len(refs), f"{case_id}: invalid claim/source gold refs")
        pair_keys: set[tuple[str, str]] = set()
        for pair in gold["expected_conflict_pairs"]:
            _require(isinstance(pair, list) and len(pair) == 2, f"{case_id}: malformed gold conflict pair")
            key = _pair_key(*pair)
            _require(key[0] in gold_claim_ids and key[1] in gold_claim_ids, f"{case_id}: conflict refs unknown claims")
            _require(key not in pair_keys, f"{case_id}: duplicate gold conflict")
            pair_keys.add(key)
        # Validate the public API request contract without leaking any labels.
        EvidenceRealityStateRequest.model_validate(
            {
                "task": case["task"],
                "entity": case["entity"],
                "documents": documents,
                "freshness_max_age_seconds": case["freshness_max_age_seconds"],
            }
        )
    _require(set(seen_scenarios) == SCENARIOS, "all six scenario categories required")
    return raw


def run_baseline(path: Path = DATASET_PATH, *, include_cases: bool = True) -> dict[str, Any]:
    """Execute the product pipeline without feeding its oracle labels to it.

    A failed performance metric is REPORT DATA, not a test failure.
    Exceptions and corrupt fixture schemas remain hard execution failures.
    """
    dataset = load_dataset(path)
    now = datetime.fromisoformat(dataset["evaluation_clock_utc"].replace("Z", "+00:00"))
    deps = replace(
        OrchestrationDependencies.default(),
        source_freshness_evaluator=SourceFreshnessEvaluator(clock=lambda: now),
        reality_state_builder=RealityStateBuilder(clock=lambda: now),
    )
    totals: Counter[str] = Counter()
    scenarios: dict[str, Counter[str]] = {scenario: Counter() for scenario in sorted(SCENARIOS)}
    results: list[dict[str, Any]] = []
    for case in dataset["cases"]:
        # Only public request fields go to the product. The gold truth never
        # enters evidence text, provenance, confidence, or the API contract.
        request = EvidenceRealityStateRequest.model_validate(
            {
                "task": case["task"],
                "entity": case["entity"],
                "documents": case["documents"],
                "freshness_max_age_seconds": case["freshness_max_age_seconds"],
            }
        )
        state = build_reality_state_from_evidence(
            request.task,
            [document.model_dump() for document in request.documents],
            freshness_max_age_seconds=request.freshness_max_age_seconds,
            entity=request.entity,
            dependencies=deps,
        )
        RealityStateResponse.model_validate(state)
        predicted = {
            _claim_key(item["text"]): set(item["source_refs"])
            for item in state["claims"]["claims"]
        }
        gold = {
            _claim_key(item["text"]): set(item["source_refs"])
            for item in case["gold"]["expected_claims"]
        }
        pred_claims = set(predicted)
        gold_claims = set(gold)
        correct_claims = pred_claims & gold_claims
        pred_links = {(claim, ref) for claim, refs in predicted.items() for ref in refs}
        gold_links = {(claim, ref) for claim, refs in gold.items() for ref in refs}
        predicted_conflicts = {
            _pair_key(item["claim_a"], item["claim_b"])
            for item in state["conflicts"]["conflicts"]
        }
        gold_conflicts = {
            _pair_key(*pair) for pair in case["gold"]["expected_conflict_pairs"]
        }
        abstain = case["gold"]["should_abstain"]
        false_support = abstain and state["status"] == "supported"
        counters = {
            "cases": 1,
            "gold_claims": len(gold_claims),
            "predicted_claims": len(pred_claims),
            "matched_claims": len(correct_claims),
            "gold_links": len(gold_links),
            "predicted_links": len(pred_links),
            "matched_links": len(gold_links & pred_links),
            "gold_conflicts": len(gold_conflicts),
            "predicted_conflicts": len(predicted_conflicts),
            "matched_conflicts": len(gold_conflicts & predicted_conflicts),
            "should_abstain": int(abstain),
            "correct_abstentions": int(abstain and state["status"] != "supported"),
            "false_supports": int(false_support),
            "safe_to_support": int(not abstain),
            "correct_supports": int(not abstain and state["status"] == "supported"),
        }
        totals.update(counters)
        scenarios[case["scenario"]].update(counters)
        results.append(
            {
                "id": case["id"],
                "scenario": case["scenario"],
                "gold_should_abstain": abstain,
                "predicted_status": state["status"],
                "false_support": bool(false_support),
                "missed_claims": sorted(gold_claims - pred_claims),
                "unexpected_claims": sorted(pred_claims - gold_claims),
                "missed_claim_source_links": len(gold_links - pred_links),
                "unexpected_claim_source_links": len(pred_links - gold_links),
                "missed_conflicts": [list(pair) for pair in sorted(gold_conflicts - predicted_conflicts)],
                "unexpected_conflicts": [list(pair) for pair in sorted(predicted_conflicts - gold_conflicts)],
            }
        )

    cp = _ratio(totals["matched_claims"], totals["predicted_claims"])
    cr = _ratio(totals["matched_claims"], totals["gold_claims"])
    lp = _ratio(totals["matched_links"], totals["predicted_links"])
    lr = _ratio(totals["matched_links"], totals["gold_links"])
    kp = _ratio(totals["matched_conflicts"], totals["predicted_conflicts"])
    kr = _ratio(totals["matched_conflicts"], totals["gold_conflicts"])
    report = {
        "dataset_id": dataset["dataset_id"],
        "fixture_type": "offline-controlled-simulated-oracle",
        "evaluation_clock_utc": dataset["evaluation_clock_utc"],
        "case_count": len(dataset["cases"]),
        "counts": dict(sorted(totals.items())),
        "metrics": {
            "claim_precision": cp,
            "claim_recall": cr,
            "claim_f1": _f1(cp, cr),
            "claim_source_precision": lp,
            "claim_source_recall": lr,
            "claim_source_f1": _f1(lp, lr),
            "conflict_precision": kp,
            "conflict_recall": kr,
            "conflict_f1": _f1(kp, kr),
            "false_support_rate": _ratio(totals["false_supports"], totals["should_abstain"]),
            "safe_abstention_rate": _ratio(totals["correct_abstentions"], totals["should_abstain"]),
            "correct_support_rate": _ratio(totals["correct_supports"], totals["safe_to_support"]),
        },
        "scenarios": {
            scenario: {
                "cases": counters["cases"],
                "false_supports": counters["false_supports"],
                "correct_abstentions": counters["correct_abstentions"],
                "matched_conflicts": counters["matched_conflicts"],
                "gold_conflicts": counters["gold_conflicts"],
            }
            for scenario, counters in sorted(scenarios.items())
        },
        "limitations": [
            "Synthetic hypothetical services, URLs, source text and independent simulated-world truth; not field-measured factual accuracy.",
            "Source labels are controlled oracles and never passed to the application as evidence.",
            "All observations are fixed replay times; not a live news or production retrieval evaluation.",
            "Source citation overlap is not entailment or publisher authentication.",
            "A false sole report cannot be discredited from one submitted document alone; those cases expose the need for independent verification.",
            "Full API input/output models are exercised, not the HTTP network transport, deployment, or latency.",
            "Improvement requires independently captured real-world documents and blinded human annotation.",
        ],
    }
    if include_cases:
        report["cases"] = results
    return report


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--dataset", type=Path, default=DATASET_PATH)
    parser.add_argument("--output", type=Path, default=None)
    parser.add_argument("--summary-only", action="store_true")
    args = parser.parse_args(argv)
    report = run_baseline(args.dataset, include_cases=not args.summary_only)
    serialized = json.dumps(report, sort_keys=True, indent=2) + "\n"
    if args.output is not None:
        args.output.write_text(serialized, encoding="utf-8")
    print(serialized, end="")
    # A poor quality result is a measurement, not a broken test runner.
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
