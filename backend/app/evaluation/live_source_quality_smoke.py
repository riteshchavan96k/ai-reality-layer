"""Step 222: operator-approved, live publisher HTTPS/Reality State canary.

A real HTTPS transaction is required; this is NOT a mocked reader benchmark.
The target is fixed and must ALSO be explicitly allowlisted by the backend.
No credentials, arbitrary URLs, source body or user input are printed/stored.
This is one historical publication observation, NOT factual truth assurance.
"""

from __future__ import annotations

import argparse
from datetime import datetime, timezone
import json
from pathlib import Path
import re
from typing import Any

from fastapi.testclient import TestClient

from backend.app.main import app
from backend.app.orchestrator.dependencies import OrchestrationDependencies
from backend.app.reality.allowlisted_https_source_reader import AllowlistedHttpsSourceReader


# Fixed, reviewed target: intentionally no arbitrary target CLI flag.
PUBLISHER_URL = "https://www.python.org/downloads/release/python-3130/"
EXPECTED_EXCERPT = "This is the stable release of Python 3.13.0"
HISTORICAL_DATE_TEXT = "Release date: Oct. 7, 2024"
FORGED_EXCERPT = "Python 3.13.0 was released on January 1, 1900."
ENTITY = "Python 3.13.0"
SHA256_PATTERN = re.compile(r"[0-9a-f]{64}")


def _request(excerpt: str, observed_at: str) -> dict[str, Any]:
    return {
        "task": "What does the original Python 3.13.0 release page say?",
        "entity": ENTITY,
        "documents": [
            {"uri": PUBLISHER_URL, "content": excerpt, "observed_at": observed_at}
        ],
        "freshness_max_age_seconds": 3600,
        "require_independent_source_text_match": True,
    }


def _checked_capture(capture: Any) -> dict[str, Any]:
    if not isinstance(capture, dict) or capture.get("uri") != PUBLISHER_URL:
        raise RuntimeError("live capture did not preserve source identity")
    content = capture.get("content")
    if not isinstance(content, str) or (
        EXPECTED_EXCERPT not in content or HISTORICAL_DATE_TEXT not in content
    ):
        raise RuntimeError("live page did not contain both independently declared anchors")
    digest = capture.get("capture_sha256")
    observed = capture.get("capture_observed_at")
    if not isinstance(digest, str) or not SHA256_PATTERN.fullmatch(digest):
        raise RuntimeError("live response did not include a valid raw-byte digest")
    if not isinstance(observed, str) or not observed.endswith("Z"):
        raise RuntimeError("live response lacks a UTC observation time")
    parsed = datetime.fromisoformat(observed.replace("Z", "+00:00"))
    if parsed.tzinfo is None:
        raise RuntimeError("capture time must be timezone-aware")
    if abs((datetime.now(timezone.utc) - parsed).total_seconds()) > 300:
        raise RuntimeError("capture time is outside the five-minute live observation window")
    return {"capture_sha256": digest, "capture_observed_at": observed}


def _post_state(client: TestClient, excerpt: str, observed_at: str) -> dict[str, Any]:
    response = client.post(
        "/api/v1/reality-state/evidence", json=_request(excerpt, observed_at)
    )
    if response.status_code != 200:
        raise RuntimeError("live strict Reality State endpoint did not return HTTP 200")
    result = response.json()
    if not isinstance(result, dict):
        raise RuntimeError("live strict Reality State response is invalid")
    return result


def _check_state(
    result: dict[str, Any],
    *,
    expected_status: str,
    expected_assurance: str,
    expected_reason: str | None,
) -> dict[str, Any]:
    assurance = result.get("evidence", {}).get("independent_source_text_assurance")
    if not isinstance(assurance, dict):
        raise RuntimeError("strict response omitted source assurance")
    sources = assurance.get("sources")
    if not isinstance(sources, list) or len(sources) != 1:
        raise RuntimeError("strict response had invalid per-source audit")
    item = sources[0]
    if (
        result.get("status") != expected_status
        or assurance.get("status") != expected_assurance
        or item.get("reason") != expected_reason
        or assurance.get("publisher_authenticated") is not False
        or assurance.get("semantic_support_verified") is not False
    ):
        raise RuntimeError("live Reality State diverged from conservative oracle")
    if expected_assurance == "exact_text_observed":
        if not isinstance(item.get("capture_sha256"), str) or not SHA256_PATTERN.fullmatch(
            item["capture_sha256"]
        ):
            raise RuntimeError("positive assurance did not retain a capture digest")
        if not item.get("capture_observed_at"):
            raise RuntimeError("positive assurance did not retain capture time")
    else:
        if item.get("capture_sha256") is not None:
            raise RuntimeError("failed assurance must not claim successful capture")
    return {
        "reality_state": result["status"],
        "source_text_assurance": assurance["status"],
        "reason": item["reason"],
    }


def run_live_smoke() -> dict[str, Any]:
    """Real HTTPS GET plus TWO independent live API requests, each separately fetched.

    The source content is never used as submitted evidence; both excerpts are
    fixed reviewer-declared strings. This avoids self-confirming text echoes.
    """
    # Fail BEFORE connecting when operator has not explicitly allowed one
    # and only one fixed canary URL. Do not silently enable network access.
    deps = OrchestrationDependencies.default()
    reader = deps.independent_source_text_assurance._reader
    if not isinstance(reader, AllowlistedHttpsSourceReader):
        raise RuntimeError("operator-configured HTTPS reader is required")
    if reader._allowed != frozenset({PUBLISHER_URL}):
        raise RuntimeError("live smoke requires exactly the fixed publisher URL allowlist")

    capture_audit = _checked_capture(reader(PUBLISHER_URL))
    with TestClient(app) as client:
        positive = _post_state(client, EXPECTED_EXCERPT, capture_audit["capture_observed_at"])
        forged = _post_state(client, FORGED_EXCERPT, capture_audit["capture_observed_at"])

    legitimate = _check_state(
        positive, expected_status="supported",
        expected_assurance="exact_text_observed", expected_reason=None,
    )
    malicious = _check_state(
        forged, expected_status="uncertain",
        expected_assurance="unverified",
        expected_reason="submitted_text_not_in_observed_content",
    )
    # Only audited metadata/decisions: do NOT write raw publisher HTML or text,
    # requester contents, full HTTP response, or secrets to CI artifacts.
    return {
        "dataset_id": "step222-one-publisher-live-https-canary-v1",
        "corpus_type": "live_original_https_page_not_publisher_authenticated",
        "publisher_url": PUBLISHER_URL,
        "capture": capture_audit,
        "scenario_count": 2,
        "legitimate_excerpt": legitimate,
        "forged_same_url_excerpt": malicious,
        "legitimate_supported": 1,
        "forged_supported": 0,
        "publisher_authenticated": False,
        "semantic_support_verified": False,
        "real_world_factual_accuracy_established": False,
        "limitations": [
            "Single historical publisher page, two declared challenge excerpts and three live HTTPS reads.",
            "Page text may change; this smoke test is intentionally fail-closed on drift or downtime.",
            "Source byte SHA256 is not a cryptographic publisher signature.",
            "Observed exact text alone does not establish semantic entailment or real-world truth.",
            "A single canary cannot estimate population-level accuracy or production reliability.",
            "No raw publisher HTML has been archived or independently human-annotated.",
        ],
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--live", action="store_true",
        help="Explicit permission to make bounded HTTPS requests to the fixed publisher URL",
    )
    parser.add_argument("--output", type=Path)
    args = parser.parse_args(argv)
    if not args.live:
        parser.error("network disabled by default; explicit --live required")
    try:
        report = run_live_smoke()
        serialized = json.dumps(report, indent=2, sort_keys=True) + "\n"
        if args.output is not None:
            args.output.write_text(serialized, encoding="utf-8")
        print(serialized, end="")
        return 0
    except Exception as exc:
        # Print only backend-authored fixed reasons, never raw network errors.
        safe_reasons = frozenset({
            "live capture did not preserve source identity",
            "live page did not contain both independently declared anchors",
            "live response did not include a valid raw-byte digest",
            "live response lacks a UTC observation time",
            "capture time must be timezone-aware",
            "capture time is outside the five-minute live observation window",
            "live strict Reality State endpoint did not return HTTP 200",
            "live strict Reality State response is invalid",
            "strict response omitted source assurance",
            "strict response had invalid per-source audit",
            "live Reality State diverged from conservative oracle",
            "positive assurance did not retain a capture digest",
            "positive assurance did not retain capture time",
            "failed assurance must not claim successful capture",
            "operator-configured HTTPS reader is required",
            "live smoke requires exactly the fixed publisher URL allowlist",
            "source HTTP response was not 200",
            "source response exceeds byte limit",
            "compressed source responses not supported",
            "unsupported source media type",
            "unsupported source character encoding",
            "source DNS returned a non-global address",
            "invalid or oversized observed source text",
        })
        reason = str(exc) if str(exc) in safe_reasons else type(exc).__name__
        print("Step 222 live publisher smoke failed: " + reason)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
