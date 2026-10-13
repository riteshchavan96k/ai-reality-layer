"""Step240: real Python.org HTTPS -> authenticated API -> bounded handoff -> neural veto.

Explicit --live only. Real model, real publisher TLS, no source text, tokens,
or raw model errors in logs; only bounded yes/no audit flags.
"""

from __future__ import annotations

import argparse
import json
import os
from pathlib import Path
import secrets
from unittest.mock import patch

from fastapi.testclient import TestClient

from backend.app.api.original_source_claim import OriginalSourceClaimRequest
from backend.app.evaluation.step237_nli_shadow import load_reviewed_model
from backend.app.integrations.semantic_veto import check_claim_with_semantic_veto
from backend.app.main import app

SOURCE = "https://www.python.org/downloads/release/python-3130/"


def run_live(*, cache_dir: Path) -> dict:
    model = load_reviewed_model(cache_dir=cache_dir, live=True)
    token = secrets.token_urlsafe(48)
    variables = {
        "ARL_RUNTIME_MODE": "pilot",
        "ARL_PILOT_BEARER_TOKEN": token,
        "ARL_INDEPENDENT_SOURCE_ALLOWED_URLS": json.dumps([SOURCE]),
    }

    def request(text: str, source: str = SOURCE) -> OriginalSourceClaimRequest:
        return OriginalSourceClaimRequest(
            entity="Python 3.13.0", source_uri=source,
            claim_text=text, freshness_max_age_seconds=3600,
        )

    with patch.dict(os.environ, variables):
        with TestClient(app) as client:
            direct = check_claim_with_semantic_veto(
                client, token, request("Python 3.13.0 is a stable release."),
                model=model,
            )
            negated = check_claim_with_semantic_veto(
                client, token, request("Python 3.13.0 is not a stable release."),
                model=model,
            )
            unsupported = check_claim_with_semantic_veto(
                client, token, request("Python 3.13.0 is a production-ready release."),
                model=model,
            )
            wrong_auth = check_claim_with_semantic_veto(
                client, token + "x", request("Python 3.13.0 is a stable release."),
                model=model,
            )
    if not (
        direct.decision == "bounded_supported"
        and direct.may_use_as_bounded_evidence is True
        and direct.reason_code == "neural_entailment_agrees"
        and direct.original_capture_sha256 is not None
        and direct.selected_text_sha256 is not None
        and negated.decision == "bounded_contradicted"
        and negated.may_use_as_bounded_evidence is False
        and unsupported.decision == "abstain"
        and wrong_auth.decision == "abstain"
        and all(not x.semantic_truth_verified
                and not x.publisher_authorship_verified
                and not x.neural_authorized_to_upgrade_claims
                for x in (direct, negated, unsupported, wrong_auth))
    ):
        raise ValueError("authenticated_original_source_neural_veto_contract_failed")
    return {
        "milestone": "step240_authenticated_bound_evidence_semantic_veto",
        "independent_python_org_https": True,
        "real_authenticated_fastapi": True,
        "real_pretrained_neural_onnx_inference": True,
        "request_bound_source_evidence": True,
        "same_source_capture_receipt": True,
        "supported_decision_only_retained_not_promoted": True,
        "original_source_contradiction_not_upgraded": True,
        "unsupported_semantic_claim_abstained": True,
        "invalid_auth_abstained": True,
        "semantic_truth_verified": False,
        "publisher_authorship_verified": False,
        "model_authorized_to_upgrade_claims": False,
        "production_backend_neural_dependencies_added": False,
        "externally_deployed": False,
        "independent_domain_accuracy_established": False,
    }


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--live", action="store_true")
    parser.add_argument("--cache-dir", type=Path, default=Path("/tmp/arl-step240-model-cache"))
    args = parser.parse_args(argv)
    if not args.live:
        parser.error("network and model download disabled; explicit --live required")
    try:
        print(json.dumps(run_live(cache_dir=args.cache_dir), sort_keys=True))
        return 0
    except Exception:
        print("Step 240 authenticated original-source neural veto check failed")
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
