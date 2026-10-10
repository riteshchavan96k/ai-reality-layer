"""Step 226: independently reviewed two-publisher real HTTPS quality smoke.

Fixed original publisher URLs; real DNS/IP-pinned TLS/HTTP is mandatory for
--live. This exercises the existing strict FastAPI source-assurance pipeline.
No arbitrary user URL, credentials, proxy, response HTML, or source body is
written to the audit. Source-text presence is NOT proof of factual truth.
"""

from __future__ import annotations

import argparse
from datetime import datetime, timezone
from hashlib import sha256
import json
from pathlib import Path
import re
from typing import Any
from urllib.parse import urlsplit

from fastapi.testclient import TestClient

from backend.app.main import app
from backend.app.orchestrator.dependencies import OrchestrationDependencies
from backend.app.reality.allowlisted_https_source_reader import AllowlistedHttpsSourceReader


PUBLISHERS = (
    {
        "id": "python-org-release",
        "url": "https://www.python.org/downloads/release/python-3130/",
        "host": "www.python.org",
        "entity": "Python 3.13.0",
        "task": "What does the official Python 3.13.0 release page state?",
        "positive": "This is the stable release of Python 3.13.0",
        "forged": "Python 3.13.0 was released on January 1, 1900.",
        "anchors": ("This is the stable release of Python 3.13.0", "Release date: Oct. 7, 2024"),
    },
    {
        "id": "iana-reserved-domains",
        "url": "https://www.iana.org/domains/reserved",
        "host": "www.iana.org",
        "entity": "example.com",
        "task": "What does IANA say about example.com and example.org?",
        "positive": (
            "a number of domains such as example.com and example.org "
            "are maintained for documentation purposes."
        ),
        "forged": "example.com and example.org are available for registration or transfer.",
        "anchors": (
            "IANA-managed Reserved Domains",
            "a number of domains such as example.com and example.org are maintained for documentation purposes.",
        ),
    },
)
APPROVED_URLS = frozenset(item["url"] for item in PUBLISHERS)
SHA256_PATTERN = re.compile(r"[0-9a-f]{64}")


class SmokeGateError(RuntimeError):
    """An explicitly authored audit-only diagnostic with no source bytes."""


def _check_receipt(source: dict[str, str], capture: Any) -> dict[str, str]:
    if not isinstance(capture, dict) or capture.get("uri") != source["url"]:
        raise SmokeGateError("publisher_source_uri_mismatch")
    content = capture.get("content")
    if not isinstance(content, str):
        raise SmokeGateError("publisher_content_unavailable_" + source["id"])
    for i, anchor in enumerate(source["anchors"]):
        if anchor not in content:
            # Probe ONLY fixed, reviewed snippets using booleans. Never
            # print original publisher body, other page contents or secrets.
            candidates = (
                "example.com and example.org",
                "They are not available for registration or transfer.",
                "These domains may be used as illustrative examples",
                "maintained for documentation purposes.",
                "a number of domains such as",
                "documentation purposes.",
                "a number of domains such as example.com and example.org",
                "number of domains such as example.com and example.org",
                "example.com and example.org are maintained",
                "example.org are maintained",
                "example.org are",
                "example.org\\nare maintained",
                "are maintained for documentation purposes.",
                "example.com and example.org are",
            ) if source["id"] == "iana-reserved-domains" else ()
            flags = "".join("1" if s in content else "0" for s in candidates)
            raise SmokeGateError(
                "publisher_content_anchor_drift_" + source["id"]
                + "_anchor_" + str(i) + "_fixed_candidates_" + flags
            )
    digest = capture.get("capture_sha256")
    observed = capture.get("capture_observed_at")
    if not isinstance(digest, str) or not SHA256_PATTERN.fullmatch(digest):
        raise SmokeGateError("invalid_source_wire_sha256")
    if not isinstance(observed, str) or not observed.endswith("Z"):
        raise SmokeGateError("invalid_capture_timestamp")
    try:
        capture_time = datetime.fromisoformat(observed.replace("Z", "+00:00"))
    except ValueError as exc:
        raise SmokeGateError("invalid_capture_timestamp") from exc
    if (
        capture_time.tzinfo is None
        or abs((datetime.now(timezone.utc) - capture_time).total_seconds()) > 300
    ):
        raise SmokeGateError("capture_timestamp_out_of_live_window")
    return {"capture_sha256": digest, "capture_observed_at": observed}


def _document(source: dict[str, str], *, authentic: bool) -> dict[str, str]:
    # The excerpts are fixed and reviewed BEFORE observing the live source.
    # We never echo retrieved HTML or its content into a submitted document.
    return {
        "uri": source["url"],
        "content": source["positive"] if authentic else source["forged"],
        # Omit client timestamp deliberately; Step 223 capture is authoritative.
    }


def _request(
    selections: tuple[tuple[dict[str, str], bool], ...],
) -> dict[str, Any]:
    return {
        "task": (
            selections[0][0]["task"]
            if len(selections) == 1 else "What do these two official publisher pages say?"
        ),
        "entity": selections[0][0]["entity"] if len(selections) == 1 else None,
        "documents": [
            _document(source, authentic=authentic)
            for source, authentic in selections
        ],
        "freshness_max_age_seconds": 3600,
        "require_independent_source_text_match": True,
    }


def _case(
    client: TestClient, key: str,
    selections: tuple[tuple[dict[str, str], bool], ...],
) -> dict[str, Any]:
    response = client.post(
        "/api/v1/reality-state/evidence", json=_request(selections)
    )
    if response.status_code != 200:
        raise SmokeGateError("reality_state_api_non_200")
    result = response.json()
    if not isinstance(result, dict):
        raise SmokeGateError("invalid_reality_state_response")
    expected_status = (
        "supported" if all(authentic for _, authentic in selections) else "uncertain"
    )
    if result.get("status") != expected_status:
        raise SmokeGateError("reality_state_oracle_mismatch")
    assurance = result.get("evidence", {}).get("independent_source_text_assurance")
    if not isinstance(assurance, dict):
        raise SmokeGateError("missing_independent_assurance")
    if (
        assurance.get("publisher_authenticated") is not False
        or assurance.get("semantic_support_verified") is not False
    ):
        raise SmokeGateError("unsupported_source_authenticity_claim")
    rows = assurance.get("sources")
    expected = {source["url"]: authentic for source, authentic in selections}
    if (
        not isinstance(rows, list)
        or len(rows) != len(selections)
        or assurance.get("source_count") != len(selections)
        or len({row.get("source_ref") for row in rows if isinstance(row, dict)})
        != len(selections)
    ):
        raise SmokeGateError("per_source_audit_identity_mismatch")
    by_uri = {
        row["source_ref"]: row for row in rows if isinstance(row, dict)
    }
    if set(by_uri) != set(expected):
        raise SmokeGateError("per_source_audit_identity_mismatch")
    observations = result.get("source_observation", {}).get("observations", [])
    if not isinstance(observations, list):
        raise SmokeGateError("invalid_capture_observation_provenance")
    times = []
    for source, authentic in selections:
        audit = by_uri[source["url"]]
        if authentic:
            if (
                audit.get("status") != "exact_text_observed"
                or audit.get("reason") is not None
            ):
                raise SmokeGateError("valid_source_excerpt_not_independently_observed")
            digest = audit.get("capture_sha256")
            if not isinstance(digest, str) or not SHA256_PATTERN.fullmatch(digest):
                raise SmokeGateError("valid_excerpt_missing_wire_digest")
            when = audit.get("capture_observed_at")
            if not isinstance(when, str) or not when.endswith("Z"):
                raise SmokeGateError("valid_excerpt_missing_capture_time")
            times.append(when)
        elif (
            audit.get("status") != "unverified"
            or audit.get("reason") != "submitted_text_not_in_observed_content"
            or audit.get("capture_sha256") is not None
        ):
            raise SmokeGateError("forged_excerpt_wrong_source_audit")
    if len(selections) == 1 and selections[0][1]:
        if (
            len(observations) != 1
            or observations[0].get("observation_method") != "independent_source_capture"
            or observations[0].get("observed_at") != times[0]
        ):
            raise SmokeGateError("invalid_capture_observation_provenance")
    return {
        "scenario_id": key,
        "source_ids": [source["id"] for source, _ in selections],
        "expected_supported": expected_status == "supported",
        "reality_state": result["status"],
        "assurance": assurance["status"],
        "verified_source_count": assurance.get("matched_source_count"),
    }


def run_live_smoke() -> dict[str, Any]:
    deps = OrchestrationDependencies.default()
    reader = deps.independent_source_text_assurance._reader
    if not isinstance(reader, AllowlistedHttpsSourceReader):
        raise SmokeGateError("operator_https_reader_required")
    if reader._allowed != APPROVED_URLS:
        raise SmokeGateError("exact_two_publisher_allowlist_required")
    if len(APPROVED_URLS) != 2 or len(
        {urlsplit(url).hostname for url in APPROVED_URLS}
    ) != 2:
        raise SmokeGateError("publisher_hosts_not_independent")
    captures = {}
    for source in PUBLISHERS:
        captures[source["id"]] = _check_receipt(
            source, reader(source["url"])
        )

    scenarios = []
    with TestClient(app) as client:
        for source in PUBLISHERS:
            scenarios.append(_case(
                client, source["id"] + "-authentic",
                ((source, True),),
            ))
            scenarios.append(_case(
                client, source["id"] + "-forged",
                ((source, False),),
            ))
        scenarios.append(_case(
            client, "both-publishers-authentic",
            tuple((source, True) for source in PUBLISHERS),
        ))
        scenarios.append(_case(
            client, "mixed-one-forged",
            ((PUBLISHERS[0], True), (PUBLISHERS[1], False)),
        ))
    supported = sum(case["reality_state"] == "supported" for case in scenarios)
    refused = sum(case["reality_state"] == "uncertain" for case in scenarios)
    if (supported, refused) != (3, 3):
        raise SmokeGateError("quality_scorecard_case_count_mismatch")
    return {
        "dataset_id": "step226-two-independent-publisher-live-https-v1",
        "corpus_type": "original_live_https_observations_predeclared_excerpts",
        "publisher_count": len(PUBLISHERS),
        "publisher_ids": [source["id"] for source in PUBLISHERS],
        "publisher_urls": [source["url"] for source in PUBLISHERS],
        "captures": captures,
        "scenario_count": len(scenarios),
        "authentic_cases_supported": supported,
        "forged_cases_supported": 0,
        "conservative_refusals": refused,
        "cases": scenarios,
        "publisher_authenticated": False,
        "semantic_support_verified": False,
        "population_factual_accuracy_established": False,
        "limitations": [
            "Two approved publisher pages, six fixed challenge cases, not a random or blinded corpus.",
            "Direct DNS/TLS/HTTPS observation is not cryptographic publisher content signing.",
            "Exact excerpt observation is not semantic entailment or independent factual truth.",
            "No original HTML is archived; only capture time and SHA256 are reported.",
            "Page changes, refusal, source downtime or network errors fail this opt-in check.",
            "The test is not evidence of generalization, production deployment or field reliability.",
        ],
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
        serialized = json.dumps(result, indent=2, sort_keys=True) + "\n"
        if args.output is not None:
            args.output.write_text(serialized, encoding="utf-8")
        print(serialized, end="")
        return 0
    except SmokeGateError as exc:
        # All explicit gate labels above are trusted fixed strings.
        print("Step 226 live publisher smoke failed: " + str(exc))
        return 1
    except Exception:
        # Never serialize arbitrary transport/provider exceptions.
        print("Step 226 live publisher smoke failed: reader_or_api_unavailable")
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
