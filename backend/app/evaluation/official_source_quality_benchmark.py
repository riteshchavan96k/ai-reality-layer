"""Step 218: official-publisher-anchored, offline adversarial Reality State replay.

Eight checked historical release dates, independently authored summaries,
and 48 labeled experiments. URLs do NOT authenticate caller-supplied text.
No runtime network use, blind human review, original HTML snapshot, or field
truth verification is claimed by this benchmark.
"""

from __future__ import annotations

import argparse
from collections import Counter
from dataclasses import replace
from datetime import datetime
import json
from pathlib import Path
from typing import Any
from urllib.parse import urlsplit

from backend.app.api.evidence_reality_state import EvidenceRealityStateRequest
from backend.app.api.reality_state import RealityStateResponse
from backend.app.orchestrator.dependencies import OrchestrationDependencies
from backend.app.orchestrator.orchestrator import build_reality_state_from_evidence
from backend.app.reality.reality_state_builder import RealityStateBuilder
from backend.app.reality.source_freshness_evaluator import SourceFreshnessEvaluator


DATASET_PATH = (
    Path(__file__).resolve().parents[2]
    / "evaluation_fixtures"
    / "step218_official_anchored_v1.json"
)
DATASET_ID = "step218-official-release-anchored-v1"
SCENARIOS = (
    "publisher_relevant",
    "url_content_tampering",
    "irrelevant_official_page",
    "explicit_synthetic_conflict",
    "stale_source_observation",
    "no_declared_freshness_policy",
)
PUBLISHER_HOSTS = frozenset({
    "www.python.org", "nodejs.org", "go.dev",
    "blog.rust-lang.org", "kubernetes.io",
})


def _require(ok: bool, reason: str) -> None:
    if not ok:
        raise ValueError("invalid Step 218 evaluation fixture: " + reason)


def _ratio(a: int, b: int) -> float | None:
    return a / b if b else None


def load_dataset(path: Path = DATASET_PATH) -> dict[str, Any]:
    dataset = json.loads(Path(path).read_text(encoding="utf-8"))
    _require(isinstance(dataset, dict), "root object required")
    _require(dataset.get("dataset_id") == DATASET_ID, "dataset ID mismatch")
    _require(dataset.get("schema_version") == "1.0", "schema version mismatch")
    _require(dataset.get("replay_time_is_synthetic") is True, "synthetic time disclosure missing")
    _require("not a verbatim" in str(dataset.get("source_format", "")).lower(), "paraphrase disclosure missing")
    _require("no second blinded human annotator" in str(dataset.get("source_review_process", "")).lower(), "independent review disclosure missing")
    for key in ("replay_clock_utc", "recent_observation_utc", "old_observation_utc"):
        value = datetime.fromisoformat(dataset[key].replace("Z", "+00:00"))
        _require(value.tzinfo is not None, f"{key} must be timezone-aware")
    anchors = dataset.get("anchors")
    cases = dataset.get("cases")
    _require(isinstance(anchors, list) and len(anchors) == 8, "exactly eight anchors required")
    _require(isinstance(cases, list) and len(cases) == 48, "exactly 48 evaluation cases required")
    anchors_by_id: dict[str, dict[str, Any]] = {}
    source_urls: set[str] = set()
    for anchor in anchors:
        _require(isinstance(anchor, dict), "anchor must be a mapping")
        name = anchor.get("id")
        _require(isinstance(name, str) and name and name not in anchors_by_id, "unique anchor IDs required")
        url = anchor.get("uri")
        parsed = urlsplit(str(url))
        _require(
            parsed.scheme == "https" and parsed.hostname in PUBLISHER_HOSTS
            and not parsed.username and not parsed.password and not parsed.fragment
            and url not in source_urls,
            f"{name}: official publisher URL required",
        )
        source_urls.add(url)
        _require(anchor.get("reviewed_by") == "assistant_source_review_not_independent_human", f"{name}: provenance review disclosure required")
        _require("not a verbatim source capture" in str(anchor.get("review_annotation", "")).lower(), f"{name}: source summary limitations required")
        statement = anchor.get("statement")
        _require(isinstance(statement, str) and statement.endswith("."), f"{name}: statement required")
        _require(anchor.get("entity") in statement, f"{name}: entity must match statement")
        date = datetime.fromisoformat(anchor["release_date"]).date()
        _require(str(date.year) in statement, f"{name}: historical date must appear in statement")
        anchors_by_id[name] = anchor
    case_ids: set[str] = set()
    observed = Counter()
    for case in cases:
        _require(isinstance(case, dict), "case must be a mapping")
        case_id = case.get("id")
        _require(isinstance(case_id, str) and case_id and case_id not in case_ids, "unique case IDs required")
        case_ids.add(case_id)
        source = case.get("anchor_id")
        scenario = case.get("scenario")
        _require(source in anchors_by_id, f"{case_id}: unknown official source")
        _require(scenario in SCENARIOS, f"{case_id}: invalid scenario")
        _require((source, scenario) not in observed, f"{case_id}: duplicate source/scenario")
        observed[(source, scenario)] += 1
        oracle = case.get("oracle")
        _require(isinstance(oracle, dict), f"{case_id}: oracle missing")
        _require(type(oracle.get("should_abstain")) is bool, f"{case_id}: abstention label missing")
        _require(oracle["should_abstain"] == (scenario != "publisher_relevant"), f"{case_id}: inconsistent review label")
        _require(isinstance(oracle.get("reason"), str) and oracle["reason"].strip(), f"{case_id}: review reason missing")
        _require("no blinded human verification" in oracle.get("label_authority", ""), f"{case_id}: missing review-limit disclosure")
    _require(len(observed) == 48, "each publisher must cover six different scenarios")
    return dataset


def _build_input(
    case: dict[str, Any],
    anchor: dict[str, Any],
    anchor_order: list[dict[str, Any]],
    dataset: dict[str, Any],
) -> dict[str, Any]:
    """Create source documents with NO oracle fields in production input."""
    scenario = case["scenario"]
    good_doc = {
        "uri": anchor["uri"],
        "title": f"{anchor['publisher']} release announcement (reviewer-authored summary)",
        "content": anchor["statement"],
        "observed_at": dataset["recent_observation_utc"],
    }
    docs = [good_doc]
    policy = 3600
    if scenario == "url_content_tampering":
        # Deliberate attacker-supplied substitution under a *real* URL.
        # The string is fabricated, NOT publisher-authored content.
        docs = [{**good_doc, "content": "Not " + anchor["statement"]}]
    elif scenario == "irrelevant_official_page":
        idx = next(i for i, item in enumerate(anchor_order) if item["id"] == anchor["id"])
        other = anchor_order[(idx + 1) % len(anchor_order)]
        docs = [{
            "uri": other["uri"],
            "title": f"{other['publisher']} release announcement (different target)",
            "content": other["statement"],
            "observed_at": dataset["recent_observation_utc"],
        }]
    elif scenario == "explicit_synthetic_conflict":
        docs.append({
            "uri": f"https://fixtures.example.test/step218/{anchor['id']}/synthetic-denial",
            "title": "SYNTHETIC ADVERSARIAL TEST CLAIM, NOT REAL PUBLISHER CONTENT",
            "content": "Not " + anchor["statement"],
            "observed_at": dataset["recent_observation_utc"],
        })
    elif scenario == "stale_source_observation":
        docs = [{**good_doc, "observed_at": dataset["old_observation_utc"]}]
    elif scenario == "no_declared_freshness_policy":
        policy = None
    return {
        "task": f"What was the historical release date of {anchor['entity']}?",
        "entity": anchor["entity"],
        "documents": docs,
        "freshness_max_age_seconds": policy,
    }


def run_baseline(path: Path = DATASET_PATH, *, include_cases: bool = True) -> dict[str, Any]:
    dataset = load_dataset(path)
    anchors = dataset["anchors"]
    by_id = {item["id"]: item for item in anchors}
    now = datetime.fromisoformat(dataset["replay_clock_utc"].replace("Z", "+00:00"))
    deps = replace(
        OrchestrationDependencies.default(),
        source_freshness_evaluator=SourceFreshnessEvaluator(clock=lambda: now),
        reality_state_builder=RealityStateBuilder(clock=lambda: now),
    )
    totals: Counter[str] = Counter()
    scenarios: dict[str, Counter[str]] = {scenario: Counter() for scenario in SCENARIOS}
    results = []
    for case in dataset["cases"]:
        anchor = by_id[case["anchor_id"]]
        request = EvidenceRealityStateRequest.model_validate(
            _build_input(case, anchor, anchors, dataset)
        )
        state = build_reality_state_from_evidence(
            request.task,
            [doc.model_dump() for doc in request.documents],
            freshness_max_age_seconds=request.freshness_max_age_seconds,
            entity=request.entity,
            dependencies=deps,
        )
        RealityStateResponse.model_validate(state)
        should_abstain = case["oracle"]["should_abstain"]
        false_supported = should_abstain and state["status"] == "supported"
        wrong_topic = case["scenario"] == "irrelevant_official_page"
        claims = state["claims"]["claims"]
        topic_matches = all(
            anchor["entity"].casefold() in claim["text"].casefold()
            for claim in claims
        ) if claims else False
        counters = Counter({
            "cases": 1,
            "should_abstain": int(should_abstain),
            "safe_to_support": int(not should_abstain),
            "false_supports": int(false_supported),
            "safe_abstentions": int(should_abstain and state["status"] != "supported"),
            "correct_supports": int(not should_abstain and state["status"] == "supported"),
            "wrong_topic_cases": int(wrong_topic),
            "wrong_topic_false_supports": int(wrong_topic and false_supported),
            "conflict_expected": int(case["scenario"] == "explicit_synthetic_conflict"),
            "conflict_detected": int(case["scenario"] == "explicit_synthetic_conflict" and state["conflicts"]["conflict_count"] > 0),
        })
        totals.update(counters)
        scenarios[case["scenario"]].update(counters)
        results.append({
            "id": case["id"], "anchor_id": anchor["id"],
            "source_url": anchor["uri"],
            "scenario": case["scenario"],
            "gold_should_abstain": should_abstain,
            "predicted_status": state["status"],
            "false_support": bool(false_supported),
            "claim_count": len(claims),
            "claim_mentions_target_entity": topic_matches,
            "detected_conflicts": state["conflicts"]["conflict_count"],
            "freshness_status": state["freshness"]["status"],
            "source_content_integrity_authenticated": False,
        })
    report = {
        "dataset_id": DATASET_ID,
        "corpus_type": dataset["corpus_type"],
        "source_count": len(anchors),
        "case_count": len(results),
        "review_process": dataset["source_review_process"],
        "replay_clock_utc": dataset["replay_clock_utc"],
        "counts": dict(sorted(totals.items())),
        "metrics": {
            "false_support_rate": _ratio(totals["false_supports"], totals["should_abstain"]),
            "safe_abstention_rate": _ratio(totals["safe_abstentions"], totals["should_abstain"]),
            "correct_support_rate": _ratio(totals["correct_supports"], totals["safe_to_support"]),
            "irrelevant_evidence_false_support_rate": _ratio(totals["wrong_topic_false_supports"], totals["wrong_topic_cases"]),
            "explicit_conflict_detection_rate": _ratio(totals["conflict_detected"], totals["conflict_expected"]),
        },
        "scenarios": {
            key: {
                "cases": v["cases"],
                "false_supports": v["false_supports"],
                "safe_abstentions": v["safe_abstentions"],
            }
            for key, v in sorted(scenarios.items())
        },
        "limitations": [
            "Eight genuine first-party official publisher URLs and assistant-reviewed historical release facts, not blind independently human-annotated sources.",
            "Statements are reviewer-authored summaries, not original publisher text captures or archived immutable raw snapshots.",
            "Four scenario families manipulate evidence/timestamps or combine with synthetic data; their inputs are NOT unmodified publisher documents.",
            "Observed_at values and replay clock are synthetic reproducibility markers, not actual publisher publication or collection times.",
            "Source URI presence does not authenticate document content; the runner deliberately tests a forged content attack.",
            "Exact claims and submitted-source attribution are not semantic factual entailment, calibration, or real-world field accuracy.",
            "The runner does not fetch sources during CI; publisher URLs must be independently rechecked for updates/availability.",
        ],
    }
    if include_cases:
        report["cases"] = results
    return report


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--dataset", type=Path, default=DATASET_PATH)
    parser.add_argument("--summary-only", action="store_true")
    parser.add_argument("--output", type=Path, default=None)
    args = parser.parse_args(argv)
    report = run_baseline(args.dataset, include_cases=not args.summary_only)
    raw = json.dumps(report, sort_keys=True, indent=2) + "\n"
    if args.output is not None:
        args.output.write_text(raw, encoding="utf-8")
    print(raw, end="")
    # Quality outcomes are findings, not reasons to hide or alter results.
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
