"""Step 236: versioned *unlabeled* semantic challenge / real deterministic baseline.

This research harness is intentionally disconnected from the runtime claim
gate, live network, model downloads and authenticated API credentials. Its
dataset is developer-authored (including deliberately false excerpts paired
with real publisher URLs), NOT independently human-reviewed factual data.

Review files may provide conditional reference labels. Self-declared reviewer
identity can never establish independent human authentication or field accuracy.
"""

from __future__ import annotations

import argparse
from collections import Counter
from hashlib import sha256
import json
from pathlib import Path
import re
from typing import Any

from backend.app.reality.claim_assertion_alignment import _parse_atomic, _relationship

DATASET = Path(__file__).resolve().parents[2] / "evaluation_fixtures" / "step236_semantic_candidates_v1.json"
DATASET_ID = "step236-semantic-candidate-pairs-v1"
# Independently reproduced by the new GitHub-hosted Step 236 CLI workflow.
# Any change to the candidate evidence requires an explicit dataset v2.
FROZEN_DATASET_SHA256 = "5987acb4fb6d33b98c079c545370d9f3dfd195bcefd7da3179f0c8b184e132fa"
SCHEMA_VERSION = "1.0"
CASE_IDS = frozenset({
    "s232-python-direct-supported", "s232-python-supported-but-outside-grammar",
    "s232-python-direct-negation", "s232-python-unrelated-entity",
    "s232-python-different-property", "s232-python-hedged-claim",
    "s232-python-forged-release-date", "s232-python-partial-unit",
    "s232-iana-genuine-but-semantically-unsupported",
    "s232-iana-forged-registration", "s232-iana-genuine-unrelated",
    "s232-iana-python-text-misattribution",
    "syn-service-paraphrase", "syn-service-negation",
    "syn-launch-paraphrase", "syn-date-different",
    "syn-neutral-context", "syn-future-conditional",
    "syn-historical-temporal", "syn-entity-confound",
})
SOURCE_REFS = frozenset({
    "https://www.python.org/downloads/release/python-3130/",
    "https://www.iana.org/domains/reserved",
    "https://fixtures.example.test/semantic-pair",
})
DECLARED_ORIGINS = frozenset({
    "developer_authored_pair_using_real_publisher_url_not_capture",
    "synthetic_fictional_exercise",
})
LABELS = frozenset({"entails", "contradicts", "neutral", "uncertain"})
PREDICTIONS = frozenset({"bounded_alignment", "bounded_contradiction", "abstain"})
ID = re.compile(r"[a-zA-Z][a-zA-Z0-9_-]{2,63}")
HEX = re.compile(r"[0-9a-f]{64}")
MAX_FILE_BYTES = 128 * 1024


class SemanticEvaluationError(ValueError):
    """Fixed error type; CLI intentionally never displays untrusted user data."""


def _require(ok: bool, reason: str):
    if not ok:
        raise SemanticEvaluationError(reason)


def _read_object(path: Path) -> dict:
    if not isinstance(path, Path):
        raise SemanticEvaluationError("invalid_file_path_type")
    data = path.read_bytes()
    _require(len(data) <= MAX_FILE_BYTES, "oversized_input")
    try:
        decoded = json.loads(data)
    except (ValueError, UnicodeDecodeError):
        raise SemanticEvaluationError("invalid_json") from None
    _require(type(decoded) is dict, "invalid_json_object")
    return decoded


def _canonical_digest(value: dict) -> str:
    return sha256(
        json.dumps(
            value, sort_keys=True, separators=(",", ":"),
            ensure_ascii=True, allow_nan=False,
        ).encode("utf-8")
    ).hexdigest()


def load_candidates(path: Path = DATASET) -> dict[str, Any]:
    raw = _read_object(path)
    _require(set(raw) == {
        "dataset_id", "schema_version", "label_provenance",
        "evidence_publisher_capture_verified", "independent_human_labels_verified",
        "representative_population", "cases",
    }, "unexpected_manifest_fields")
    _require(raw["dataset_id"] == DATASET_ID and raw["schema_version"] == SCHEMA_VERSION,
             "unexpected_dataset_identity")
    _require(
        raw["label_provenance"] == "developer_authored_unreviewed_no_ground_truth"
        and raw["evidence_publisher_capture_verified"] is False
        and raw["independent_human_labels_verified"] is False
        and raw["representative_population"] is False,
        "dishonest_evidence_or_label_provenance",
    )
    cases = raw["cases"]
    _require(type(cases) is list and len(cases) == len(CASE_IDS), "unexpected_case_count")
    ids = set()
    for case in cases:
        _require(type(case) is dict and set(case) == {
            "id", "entity", "claim", "evidence_excerpt", "source_ref", "evidence_origin"
        }, "case_field_mismatch_or_gold_leak")
        case_id = case["id"]
        _require(type(case_id) is str and case_id in CASE_IDS and case_id not in ids,
                 "unknown_or_duplicate_case_id")
        ids.add(case_id)
        for name in ("entity", "claim", "evidence_excerpt"):
            value = case[name]
            _require(
                type(value) is str and 0 < len(value) <= 500
                and value.strip() == value and "\r" not in value and "\n" not in value,
                "invalid_case_text",
            )
        ref = case["source_ref"]
        origin = case["evidence_origin"]
        _require(type(ref) is str and ref in SOURCE_REFS and type(origin) is str
                 and origin in DECLARED_ORIGINS,
                 "unreviewed_or_invalid_source_provenance")
        _require(
            (case_id.startswith("s232-")
             and origin == "developer_authored_pair_using_real_publisher_url_not_capture"
             and ref != "https://fixtures.example.test/semantic-pair")
            or
            (case_id.startswith("syn-") and origin == "synthetic_fictional_exercise"
             and ref == "https://fixtures.example.test/semantic-pair"),
            "misleading_candidate_origin",
        )
    _require(ids == CASE_IDS, "case_ids_changed")
    _require(_canonical_digest(raw) == FROZEN_DATASET_SHA256,
             "frozen_dataset_digest_mismatch_requires_new_version")
    return raw


def baseline_prediction(case: dict[str, Any]) -> str:
    """Reuse today's genuine deterministic parser, not an invented NLI oracle."""
    relation = _relationship(
        _parse_atomic(case["claim"]),
        _parse_atomic(case["evidence_excerpt"]),
    )
    if relation == "aligned":
        return "bounded_alignment"
    if relation == "contradicted":
        return "bounded_contradiction"
    return "abstain"


def baseline_report(manifest: dict[str, Any]) -> dict[str, Any]:
    digest = _canonical_digest(manifest)
    rows = [
        {"case_id": item["id"], "prediction": baseline_prediction(item)}
        for item in manifest["cases"]
    ]
    return {
        "dataset_id": DATASET_ID,
        "dataset_sha256": digest,
        "candidate_count": len(rows),
        "prediction_counts": dict(sorted(Counter(x["prediction"] for x in rows).items())),
        "independent_human_labels_verified": False,
        "factual_truth_verified": False,
        "source_capture_verified": False,
        "semantic_nli_model_executed": False,
        "population_accuracy_established": False,
        "evaluation_kind": "developer-authored_text_parser_baseline_not_field_accuracy",
        "results": rows,
    }


def blind_review_packet(manifest: dict[str, Any]) -> dict[str, Any]:
    """Never leak predictions or any prior authored labels to the reviewers."""
    return {
        "schema_version": SCHEMA_VERSION,
        "dataset_id": DATASET_ID,
        "dataset_sha256": _canonical_digest(manifest),
        "independent_human_labels_verified": False,
        "review_status": "not_collected",
        "instructions": (
            "Evaluate meaning of claim relative to ONLY the displayed candidate excerpt. "
            "Choose entails, contradicts, neutral or uncertain. "
            "Do not assume the source URL authenticates the excerpt. "
            "No baseline predictions or prior developer labels are provided."
        ),
        "cases": [
            {k: case[k] for k in (
                "id", "entity", "claim", "evidence_excerpt", "source_ref", "evidence_origin"
            )} for case in manifest["cases"]
        ],
    }


def conditional_review_comparison(
    manifest: dict[str, Any],
    review_file: dict[str, Any],
) -> dict[str, Any]:
    """Never assert independence from untrusted self-declared reviewer IDs.

    Requires exactly two distinct reviewer IDs per case, consensus, the exact
    manifest digest and complete case coverage before conditional counts.
    """
    _require(type(review_file) is dict and set(review_file) == {
        "schema_version", "dataset_sha256", "review_identity_audit_status", "annotations"
    }, "unexpected_review_fields")
    _require(
        review_file["schema_version"] == SCHEMA_VERSION
        and review_file["dataset_sha256"] == _canonical_digest(manifest)
        and review_file["review_identity_audit_status"] == "not_independently_verified",
        "review_provenance_or_digest_mismatch",
    )
    annotations = review_file["annotations"]
    _require(type(annotations) is list and len(annotations) <= 2 * len(CASE_IDS),
             "invalid_review_length")
    by_case: dict[str, dict[str, str]] = {case_id: {} for case_id in CASE_IDS}
    for record in annotations:
        _require(type(record) is dict and set(record) == {
            "case_id", "reviewer_id", "label"
        }, "invalid_annotation_fields")
        case_id, reviewer, label = record["case_id"], record["reviewer_id"], record["label"]
        _require(type(case_id) is str and case_id in by_case
                 and type(reviewer) is str and ID.fullmatch(reviewer) is not None
                 and type(label) is str and label in LABELS,
                 "invalid_annotation_value")
        _require(reviewer not in by_case[case_id] and len(by_case[case_id]) < 2,
                 "duplicate_or_excess_review")
        by_case[case_id][reviewer] = label

    missing = sum(len(x) < 2 for x in by_case.values())
    disputed = sum(len(x) == 2 and len(set(x.values())) > 1 for x in by_case.values())
    base = {
        "dataset_id": DATASET_ID,
        "dataset_sha256": _canonical_digest(manifest),
        "case_count": len(CASE_IDS),
        "complete_two_review_cases": len(CASE_IDS) - missing,
        "missing_review_cases": missing,
        "disputed_cases": disputed,
        "independent_human_labels_verified": False,
        "reviewer_identity_authentication": "not_independently_verified",
        "population_accuracy_established": False,
        "factual_truth_verified": False,
    }
    if missing or disputed:
        return {
            **base, "status": "incomplete" if missing else "disputed",
            "conditional_counts": None,
        }

    consensus = {k: next(iter(v.values())) for k, v in by_case.items()}
    predicted = {c["id"]: baseline_prediction(c) for c in manifest["cases"]}
    all_ids = CASE_IDS
    return {
        **base,
        "status": "conditional_consensus_unverified_reviewer_identities",
        "conditional_counts": {
            "by_submitted_label": dict(sorted(Counter(consensus.values()).items())),
            "by_model_prediction": dict(sorted(Counter(predicted.values()).items())),
            "possible_false_support": sum(
                predicted[k] == "bounded_alignment" and consensus[k] != "entails"
                for k in all_ids
            ),
            "bounded_alignment_on_submitted_entailment": sum(
                predicted[k] == "bounded_alignment" and consensus[k] == "entails"
                for k in all_ids
            ),
            "submitted_entailment_count": sum(consensus[k] == "entails" for k in all_ids),
            "incorrect_contradictions": sum(
                predicted[k] == "bounded_contradiction"
                and consensus[k] != "contradicts" for k in all_ids
            ),
            "abstained": sum(predicted[k] == "abstain" for k in all_ids),
            "reviewed_case_count": len(all_ids),
        },
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--summary-only", action="store_true")
    parser.add_argument("--blind-packet", type=Path)
    parser.add_argument("--review-file", type=Path)
    args = parser.parse_args(argv)
    try:
        corpus = load_candidates()
        result = baseline_report(corpus)
        if args.blind_packet is not None:
            packet = blind_review_packet(corpus)
            args.blind_packet.write_text(json.dumps(packet, indent=2) + "\n", encoding="utf-8")
        if args.review_file is not None:
            result["review_comparison"] = conditional_review_comparison(
                corpus, _read_object(args.review_file)
            )
        if args.summary_only:
            result.pop("results")
        print(json.dumps(result, sort_keys=True))
        return 0
    except (OSError, ValueError, TypeError):
        print("Step 236 evaluation foundation: invalid candidate manifest or review input")
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
