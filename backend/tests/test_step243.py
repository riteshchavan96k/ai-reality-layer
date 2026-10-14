"""Step243 true FastAPI integration tests of two separately attributed HTTPS observations.

Test source bodies here are explicitly mocked and are not real publisher data.
"""
from copy import deepcopy
from datetime import datetime, timedelta, timezone
from hashlib import sha256
import json

import pytest
from fastapi.testclient import TestClient

from backend.app.api.original_source_claim import OriginalSourceClaimRequest
from backend.app.api.two_origin_answer import (
    TwoOriginAnswerRequest, two_origin_binding_sha256,
    PAIR_ALIGNED, PAIR_CONTRADICTED, PAIR_DISAGREEMENT, PAIR_ABSTAINED,
)
from backend.app.main import app
from backend.app.reality.allowlisted_https_source_reader import AllowlistedHttpsSourceReader

SOURCE1 = "https://www.python.org/downloads/release/python-3130/"
SOURCE2 = "https://www.iana.org/domains/reserved"
UNAPPROVED = "https://go.dev/dl/"
TOKEN = "step243-pilot-api-test-secret-is-at-least-32-bytes"
POSITIVE = "This is the stable release of Python 3.13.0"
NEGATIVE = "Python 3.13.0 is not a stable release."
PATH = "/api/v1/reality-state/answer/compare"

def requested(claim="Python 3.13.0 is a stable release.", *, urls=None, age=3600):
    return TwoOriginAnswerRequest(
        claim_text=claim, entity="Python 3.13.0",
        source_uris=[SOURCE1, SOURCE2] if urls is None else urls,
        freshness_max_age_seconds=age,
    )

def capture(uri, body=POSITIVE, *, when=None, quote_hashes=None):
    return {
        "uri": uri, "content": body,
        "capture_sha256": sha256(body.encode("utf-8")).hexdigest(),
        "capture_observed_at": (when or datetime.now(timezone.utc)).isoformat()
            .replace("+00:00", "Z"),
        "observed_quote_unit_sha256": quote_hashes or [],
    }

@pytest.fixture
def pilot(monkeypatch):
    monkeypatch.setenv("ARL_RUNTIME_MODE", "pilot")
    monkeypatch.setenv("ARL_PILOT_BEARER_TOKEN", TOKEN)
    monkeypatch.setenv(
        "ARL_INDEPENDENT_SOURCE_ALLOWED_URLS", json.dumps([SOURCE1, SOURCE2]),
    )
    reads = []
    current = {SOURCE1: capture(SOURCE1), SOURCE2: capture(SOURCE2)}

    def reader(self, uri):
        reads.append(uri)
        value = current[uri]
        if isinstance(value, Exception):
            raise value
        return deepcopy(value)

    monkeypatch.setattr(AllowlistedHttpsSourceReader, "__call__", reader)
    with TestClient(app) as client:
        yield client, reads, current

def post(client, request=None, token=TOKEN):
    return client.post(
        PATH, json=(requested() if request is None else request).model_dump(mode="json"),
        headers={"Authorization": "Bearer " + token},
    )

def ceiling(body):
    for key in (
        "factual_truth_verified", "publisher_authorship_verified",
        "independently_owned_publishers_verified", "neural_model_used",
        "general_question_answering",
    ):
        assert body[key] is False

def abstained(body):
    assert body["outcome"] == "abstain"
    assert body["answer_text"] == PAIR_ABSTAINED
    assert body["reason_code"] == "source_evidence_incomplete"
    assert body["may_use_as_bounded_evidence"] is False
    assert body["source_observation_count"] == 0
    assert body["distinct_https_hostnames"] is False
    assert body["citations"] == []
    assert SOURCE1 not in json.dumps(body)
    assert SOURCE2 not in json.dumps(body)
    assert POSITIVE not in json.dumps(body)
    ceiling(body)

def test_both_align_and_each_citation_bound_to_an_actual_observation(pilot):
    client, reads, current = pilot
    response = post(client)
    assert response.status_code == 200
    body = response.json()
    assert body["outcome"] == "two_source_alignment"
    assert body["reason_code"] == "two_source_aligned"
    assert body["answer_text"] == PAIR_ALIGNED
    assert body["may_use_as_bounded_evidence"] is True
    assert body["distinct_https_hostnames"] is True
    assert body["source_observation_count"] == 2
    assert body["request_binding_sha256"] == two_origin_binding_sha256(requested())
    assert [c["source_uri"] for c in body["citations"]] == [SOURCE1, SOURCE2]
    for c in body["citations"]:
        assert c["original_source_quote"] == POSITIVE
        assert c["source_quote_sha256"] == sha256(POSITIVE.encode()).hexdigest()
        assert c["source_capture_sha256"] == current[c["source_uri"]]["capture_sha256"]
        assert c["source_capture_observed_at"].endswith("Z")
    assert reads == [SOURCE1, SOURCE2]
    ceiling(body)

def test_both_contradict_and_never_promote_to_support(pilot):
    client, reads, content = pilot
    content[SOURCE1] = capture(SOURCE1, NEGATIVE)
    content[SOURCE2] = capture(SOURCE2, NEGATIVE)
    body = post(client).json()
    assert body["outcome"] == "two_source_contradiction"
    assert body["answer_text"] == PAIR_CONTRADICTED
    assert body["may_use_as_bounded_evidence"] is False
    assert len(body["citations"]) == 2
    assert reads == [SOURCE1, SOURCE2]
    ceiling(body)

@pytest.mark.parametrize("negative_source", [SOURCE1, SOURCE2])
def test_genuine_opposite_bounded_source_statements_surface_disagreement(pilot, negative_source):
    client, reads, content = pilot
    content[negative_source] = capture(negative_source, NEGATIVE)
    body = post(client).json()
    assert body["outcome"] == "source_disagreement"
    assert body["answer_text"] == PAIR_DISAGREEMENT
    assert body["reason_code"] == "two_source_disagreement"
    assert body["may_use_as_bounded_evidence"] is False
    assert len(body["citations"]) == 2
    assert reads == [SOURCE1, SOURCE2]
    ceiling(body)

@pytest.mark.parametrize("defect", [
    "unrelated_second", "stale_second", "exception_first", "exception_second",
    "wrong_identity_second", "quoted_second", "multiple_first", "bad_receipt_first",
])
def test_partial_failure_never_exposes_single_citation_or_source_url(pilot, defect):
    client, reads, content = pilot
    if defect == "unrelated_second":
        content[SOURCE2] = capture(SOURCE2, "This page describes example domains.")
    elif defect == "stale_second":
        content[SOURCE2] = capture(
            SOURCE2, when=datetime.now(timezone.utc)-timedelta(hours=3)
        )
    elif defect == "exception_first":
        content[SOURCE1] = OSError("internal_secret_marker")
    elif defect == "exception_second":
        content[SOURCE2] = OSError("internal_secret_marker")
    elif defect == "wrong_identity_second":
        content[SOURCE2] = capture(SOURCE1)
    elif defect == "quoted_second":
        content[SOURCE2] = capture(
            SOURCE2, quote_hashes=[sha256(POSITIVE.encode()).hexdigest()]
        )
    elif defect == "multiple_first":
        content[SOURCE1] = capture(SOURCE1, POSITIVE + "\n" + POSITIVE)
    elif defect == "bad_receipt_first":
        content[SOURCE1]["capture_sha256"] = "forged"
    body = post(client).json()
    abstained(body)
    assert "internal_secret_marker" not in json.dumps(body)
    assert reads in ([SOURCE1], [SOURCE1, SOURCE2])

def test_off_allowlist_second_source_is_denied_before_first_fetch(pilot):
    client, reads, _ = pilot
    abstained(post(client, requested(urls=[SOURCE1, UNAPPROVED])).json())
    assert reads == []

@pytest.mark.parametrize("urls", [
    [SOURCE1, SOURCE1],
    [SOURCE1, "https://www.python.org/downloads"],
    ["https://WWW.PYTHON.ORG/downloads", SOURCE1],
    [SOURCE1], [SOURCE1, SOURCE2, UNAPPROVED],
    [SOURCE1, "http://www.iana.org/domains/reserved"],
    [SOURCE1, "https://127.0.0.1/internal"],
])
def test_invalid_duplicate_or_dangerous_urls_fail_validation_before_fetch(pilot, urls):
    client, reads, _ = pilot
    body = {
        "claim_text": "Python 3.13.0 is a stable release.",
        "entity": "Python 3.13.0",
        "source_uris": urls,
        "freshness_max_age_seconds": 3600,
    }
    response = client.post(
        PATH, json=body, headers={"Authorization": "Bearer " + TOKEN},
    )
    assert response.status_code == 422
    assert reads == []

def test_wrong_bearer_refused_without_network(pilot):
    client, reads, _ = pilot
    assert post(client, token=TOKEN + "bad").status_code == 401
    assert reads == []

@pytest.mark.parametrize("claim", [
    "Maybe Python 3.13.0 is a stable release.",
    "Python 3.13.0 is production ready for every application.",
])
def test_unsupported_claims_abstain(pilot, claim):
    client, reads, _ = pilot
    abstained(post(client, requested(claim)).json())
    assert reads in ([], [SOURCE1])

def test_request_binding_changes_with_order_and_freshness(pilot):
    client, reads, _ = pilot
    normal = requested()
    swapped = requested(urls=[SOURCE2, SOURCE1])
    short = requested(age=60)
    assert len({two_origin_binding_sha256(x) for x in (normal, swapped, short)}) == 3
    body = post(client, swapped).json()
    assert [item["source_uri"] for item in body["citations"]] == [SOURCE2, SOURCE1]
    assert body["request_binding_sha256"] == two_origin_binding_sha256(swapped)
    assert reads == [SOURCE2, SOURCE1]

def test_previous_single_source_cited_answer_untouched(pilot):
    client, reads, _ = pilot
    request = OriginalSourceClaimRequest(
        claim_text="Python 3.13.0 is a stable release.",
        entity="Python 3.13.0", source_uri=SOURCE1,
    )
    original = client.post(
        "/api/v1/reality-state/answer", json=request.model_dump(mode="json"),
        headers={"Authorization": "Bearer " + TOKEN},
    )
    assert original.status_code == 200
    assert original.json()["outcome"] == "bounded_source_support"
    assert reads == [SOURCE1]
    assert PATH in app.openapi()["paths"]

def test_forbidden_extra_input_and_invalid_age_do_not_fetch(pilot):
    client, reads, _ = pilot
    body = requested().model_dump(mode="json")
    body["verified_by"] = "untrusted-client"
    assert client.post(
        PATH, json=body, headers={"Authorization": "Bearer " + TOKEN},
    ).status_code == 422
    body.pop("verified_by")
    body["freshness_max_age_seconds"] = -1
    assert client.post(
        PATH, json=body, headers={"Authorization": "Bearer " + TOKEN},
    ).status_code == 422
    assert reads == []
