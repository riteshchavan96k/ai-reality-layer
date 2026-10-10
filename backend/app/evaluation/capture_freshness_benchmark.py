"""Step 223: synthetic capture-vs-reported freshness adversarial replay.

NOT independent publisher truth: the backend reader is an operator-side
fixture. Verifies actual Reality State status, observation lineage and refusal
to let submitted timestamps override server-observed capture time.
"""

from dataclasses import replace
from datetime import datetime, timedelta, timezone
from hashlib import sha256
import json

from backend.app.orchestrator.dependencies import OrchestrationDependencies
from backend.app.orchestrator.orchestrator import build_reality_state_from_evidence
from backend.app.api.reality_state import RealityStateResponse
from backend.app.reality.independent_source_text_assurance import IndependentSourceTextAssurance
from backend.app.reality.source_freshness_evaluator import SourceFreshnessEvaluator
from backend.app.reality.reality_state_builder import RealityStateBuilder

URL = "https://publisher.example.test/release/3130"
CONTENT = "Python 3.13.0 was released on October 7, 2024."


def _stamp(value: datetime) -> str:
    return value.astimezone(timezone.utc).isoformat().replace("+00:00", "Z")


def run_benchmark() -> dict:
    now = datetime.now(timezone.utc) - timedelta(seconds=5)
    clock = lambda: now
    recent = _stamp(now - timedelta(seconds=10))
    old = _stamp(now - timedelta(days=7))
    reported_new = _stamp(now - timedelta(seconds=1))
    scenarios = (
        ("fresh_capture_old_caller", recent, old, "supported", "independent_source_capture"),
        ("old_capture_fresh_caller", old, reported_new, "uncertain", "independent_source_capture"),
        ("fresh_capture_no_caller", recent, None, "supported", "independent_source_capture"),
        ("no_capture_no_caller", None, None, "uncertain", None),
        ("legacy_no_capture_reported", None, reported_new, "supported", "submitted_evidence_observation"),
    )
    base = OrchestrationDependencies.default()
    results = []
    for name, capture_time, reported_time, expected, method in scenarios:
        def observer(uri):
            item = {"uri": uri, "content": CONTENT}
            if capture_time is not None:
                item.update(
                    capture_sha256=sha256(CONTENT.encode()).hexdigest(),
                    capture_observed_at=capture_time,
                )
            return item
        deps = replace(
            base,
            independent_source_text_assurance=IndependentSourceTextAssurance(observer),
            source_freshness_evaluator=SourceFreshnessEvaluator(clock=clock),
            reality_state_builder=RealityStateBuilder(clock=clock),
        )
        document = {"uri": URL, "content": CONTENT}
        if reported_time is not None:
            document["observed_at"] = reported_time
        outcome = build_reality_state_from_evidence(
            "What was the release date of Python 3.13.0?",
            [document], entity="Python 3.13.0",
            require_independent_source_text_match=True,
            freshness_max_age_seconds=3600,
            dependencies=deps,
        )
        RealityStateResponse.model_validate(outcome)
        obs = outcome["source_observation"]
        actual_method = (
            obs["observations"][0]["observation_method"]
            if obs["status"] == "usable" else None
        )
        if outcome["status"] != expected or actual_method != method:
            raise AssertionError(
                "Step 223 source freshness acceptance failed: " + name
            )
        results.append({
            "scenario": name,
            "result": outcome["status"],
            "observation_method": actual_method,
            "expected_status": expected,
        })
    return {
        "dataset_id": "step223-backend-capture-timestamp-adversarial-v1",
        "corpus_type": "backend-injected-synthetic-captures-not-live-publisher-observation",
        "case_count": len(results),
        "correct_count": len(results),
        "client_spoofed_fresh_supported_count": 0,
        "server_recent_capture_supported_count": 2,
        "cases": results,
        "publisher_authenticated": False,
        "semantic_support_verified": False,
        "limitations": [
            "Only synthetic capture/reported timestamps; not a live publisher corpus.",
            "Historical Step 217/218/220 benchmark scores remain separate.",
            "Time of content observation is not time of original publication or factual truth.",
            "Legacy backend readers without capture metadata preserve old reported-time semantics.",
        ],
    }


def main() -> int:
    print(json.dumps(run_benchmark(), sort_keys=True, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
