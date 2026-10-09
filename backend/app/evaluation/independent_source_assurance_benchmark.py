"""Step 220: controlled server-reader replay for opt-in exact source-text matching.

All observer text is author-curated from the Step 218 reviewer summaries,
NOT live original publisher HTML. This shows the gate's conditional behavior
without claiming internet source authentication or field factual accuracy.
"""

from collections import Counter
from dataclasses import replace
from datetime import datetime
import json
from pathlib import Path
from typing import Any

from backend.app.api.evidence_reality_state import EvidenceRealityStateRequest
from backend.app.api.reality_state import RealityStateResponse
from backend.app.evaluation.official_source_quality_benchmark import (
    DATASET_PATH, _build_input, load_dataset,
)
from backend.app.orchestrator.dependencies import OrchestrationDependencies
from backend.app.orchestrator.orchestrator import build_reality_state_from_evidence
from backend.app.reality.independent_source_text_assurance import IndependentSourceTextAssurance
from backend.app.reality.reality_state_builder import RealityStateBuilder
from backend.app.reality.source_freshness_evaluator import SourceFreshnessEvaluator


def run_baseline(path: Path = DATASET_PATH) -> dict[str, Any]:
    dataset = load_dataset(path)
    anchors = dataset["anchors"]
    curated = {item["uri"]: item["statement"] for item in anchors}
    # Deliberately NEVER read submitted documents in this callback.
    # The callback is an independently configured backend source of
    # reference bytes; these are fictionalized reviewer summaries,
    # NOT authenticated publisher content.
    def observer(uri: str) -> dict[str, str] | None:
        if uri not in curated:
            return None
        return {"uri": uri, "content": curated[uri]}

    now = datetime.fromisoformat(dataset["replay_clock_utc"].replace("Z", "+00:00"))
    base = OrchestrationDependencies.default()
    deps = replace(
        base,
        source_freshness_evaluator=SourceFreshnessEvaluator(clock=lambda: now),
        reality_state_builder=RealityStateBuilder(clock=lambda: now),
        independent_source_text_assurance=IndependentSourceTextAssurance(observer),
    )
    unknown_deps = replace(
        deps,
        independent_source_text_assurance=IndependentSourceTextAssurance(),
    )

    counts = Counter()
    scenarios = {name: Counter() for name in (
        "publisher_relevant", "url_content_tampering",
        "irrelevant_official_page", "explicit_synthetic_conflict",
        "stale_source_observation", "no_declared_freshness_policy",
    )}
    for case in dataset["cases"]:
        anchor = next(item for item in anchors if item["id"] == case["anchor_id"])
        request = EvidenceRealityStateRequest.model_validate(
            _build_input(case, anchor, anchors, dataset)
        )
        def run_for_dependencies(services):
            output = build_reality_state_from_evidence(
                request.task, [doc.model_dump() for doc in request.documents],
                freshness_max_age_seconds=request.freshness_max_age_seconds,
                entity=request.entity, dependencies=services,
                require_independent_source_text_match=True,
            )
            RealityStateResponse.model_validate(output)
            return output

        observed = run_for_dependencies(deps)
        unavailable = run_for_dependencies(unknown_deps)
        must_abstain = case["oracle"]["should_abstain"]
        group = scenarios[case["scenario"]]
        counts["cases"] += 1
        group["cases"] += 1
        if must_abstain:
            counts["abstain_required"] += 1
            if observed["status"] == "supported":
                counts["false_supported"] += 1
                group["false_supported"] += 1
        else:
            counts["legitimate_cases"] += 1
            if observed["status"] == "supported":
                counts["legitimate_supported"] += 1
                group["legitimate_supported"] += 1
            if unavailable["status"] == "supported":
                counts["unconfigured_legitimate_supported"] += 1

        check = observed["evidence"]["independent_source_text_assurance"]
        assert check["publisher_authenticated"] is False
        if check["status"] == "exact_text_observed":
            counts["all_source_text_observed_cases"] += 1
        if unavailable["status"] != "uncertain":
            counts["unconfigured_not_uncertain"] += 1

    ratio = lambda a, b: a / b if b else None
    return {
        "dataset_id": "step220-curated-observer-replay-v1",
        "source_dataset_id": dataset["dataset_id"],
        "corpus_type": "operator-curated-simulated-observer-text-not-publisher-authenticated",
        "case_count": counts["cases"],
        "counts": dict(sorted(counts.items())),
        "metrics": {
            "false_support_rate": ratio(counts["false_supported"], counts["abstain_required"]),
            "legitimate_support_rate": ratio(counts["legitimate_supported"], counts["legitimate_cases"]),
            "unconfigured_legitimate_support_rate": ratio(counts["unconfigured_legitimate_supported"], counts["legitimate_cases"]),
        },
        "scenarios": {name: dict(sorted(s.items())) for name, s in sorted(scenarios.items())},
        "limitations": [
            "Simulated server-controlled reader uses fixed reviewer-authored source statements from the Step 218 dataset; not actual publisher captures.",
            "Independent from submitted/forged case documents, but not independently validated by a second human or publisher cryptography.",
            "A real deployment MUST install a trusted, securely operated and bounded source reader. None is configured by default.",
            "Exact substring observation does not establish semantic truth, source authorship or cross-source corroboration.",
            "The fail-closed unconfigured mode intentionally abstains on legitimate cases as well as forged cases.",
            "Original historical Step 217/218 results and Step 219 scorecards remain unchanged in this opt-in replay.",
        ],
    }


def main(argv: list[str] | None = None) -> int:
    import argparse
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, default=None)
    args = parser.parse_args(argv)
    result = run_baseline()
    serialized = json.dumps(result, sort_keys=True, indent=2) + "\n"
    if args.output is not None:
        args.output.write_text(serialized, encoding="utf-8")
    print(serialized, end="")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
