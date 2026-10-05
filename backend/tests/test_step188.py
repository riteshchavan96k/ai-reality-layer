"""Step 188 — same bounded observation-time contract on both source paths."""

import pytest
from pydantic import ValidationError

from backend.app.api.evidence_reality_state import (
    EvidenceDocumentInput,
    EvidenceRealityStateRequest,
)
from backend.app.main import app, reality_state_from_evidence
from backend.app.orchestrator.orchestrator import build_reality_state_from_evidence
from backend.app.reality.evidence_normalizer import RetrievalEvidenceNormalizer
from backend.app.reality.http_retrieval_provider import HttpRetrievalProvider
from backend.app.reality.retrieval_input_bounds import (
    MAX_RETRIEVED_OBSERVED_AT_CHARS,
    validate_retrieved_evidence_bounds,
)
from backend.app.reality.retrieval_provider_response import RetrievalProviderResponse
from backend.app.reality.source_observation import (
    MAX_SOURCE_OBSERVED_AT_CHARS,
    SourceObservation,
    SourceObservationResult,
    normalize_reported_observation_time,
)
from backend.app.reality.submitted_evidence import SubmittedEvidenceBundle


URI = "https://example.test/original"
TEMPLATE = "https://gateway.example.test/search?q={query}"
OBSERVED = "2026-01-01T12:30:00Z"
OFFSET = "2026-01-01T18:00:00+05:30"


def _document(observed_at=OBSERVED):
    return {
        "uri": URI,
        "content": "Company X is operational.",
        "observed_at": observed_at,
    }


def _provider_payload(observed_at):
    return {
        "sources": [{
            "uri": URI,
            "content": "Company X is operational.",
            "observed_at": observed_at,
        }],
    }


def _exact_length_timestamp():
    # Whitespace is intentionally stripped in existing public timestamp
    # contracts; enforce the raw length before allocating a parsed time.
    return OBSERVED + " " * (MAX_SOURCE_OBSERVED_AT_CHARS - len(OBSERVED))


def test_retrieval_and_submitted_timestamp_bounds_share_one_source_contract():
    assert MAX_SOURCE_OBSERVED_AT_CHARS == 64
    assert MAX_RETRIEVED_OBSERVED_AT_CHARS == MAX_SOURCE_OBSERVED_AT_CHARS


def test_shared_parser_accepts_exact_raw_boundary_and_normalizes():
    raw = _exact_length_timestamp()
    assert len(raw) == MAX_SOURCE_OBSERVED_AT_CHARS
    assert normalize_reported_observation_time(raw) == OBSERVED


@pytest.mark.parametrize("size", [65, 128, 100_000])
def test_shared_parser_fails_closed_before_parsing_overlong_input(size):
    raw = OBSERVED + " " * (size - len(OBSERVED))
    with pytest.raises(ValueError, match="exceeds 64"):
        normalize_reported_observation_time(raw)


@pytest.mark.parametrize("raw", [OFFSET, " 2026-01-01T12:30:00Z "])
def test_submitted_domain_normalizes_offsets_and_whitespace(raw):
    doc = SubmittedEvidenceBundle.from_mappings([_document(raw)]).documents[0]
    assert doc.observed_at == OBSERVED
    assert doc.source_dict()["uri"] == URI
    assert doc.source_dict()["content"] == "Company X is operational."


def test_submitted_domain_accepts_exact_boundary():
    doc = SubmittedEvidenceBundle.from_mappings(
        [_document(_exact_length_timestamp())]
    ).documents[0]
    assert doc.observed_at == OBSERVED


@pytest.mark.parametrize("size", [65, 128, 100_000])
def test_submitted_domain_rejects_oversized_raw_observation(size):
    raw = OBSERVED + " " * (size - len(OBSERVED))
    with pytest.raises(ValueError, match="64 characters"):
        SubmittedEvidenceBundle.from_mappings([_document(raw)])


@pytest.mark.parametrize("size", [65, 128, 100_000])
def test_submitted_http_model_rejects_oversized_raw_observation(size):
    raw = OBSERVED + " " * (size - len(OBSERVED))
    with pytest.raises(ValidationError, match="64"):
        EvidenceRealityStateRequest(
            task="What is the current status of Company X?",
            documents=[_document(raw)],
        )


def test_submitted_http_model_accepts_raw_boundary_and_utc_offset():
    request = EvidenceRealityStateRequest(
        task="What is the current status of Company X?",
        documents=[_document(_exact_length_timestamp())],
    )
    assert request.documents[0].observed_at == OBSERVED
    offset = EvidenceDocumentInput.model_validate(_document(OFFSET))
    assert offset.observed_at == OBSERVED


def test_http_openapi_advertises_observation_character_limit():
    schema = app.openapi()["components"]["schemas"]["EvidenceDocumentInput"]
    prop = schema["properties"]["observed_at"]
    variants = prop.get("anyOf", [prop])
    assert any(
        variant.get("maxLength") == MAX_SOURCE_OBSERVED_AT_CHARS
        for variant in variants
    )


def test_http_retrieval_path_accepts_normalized_exact_boundary():
    result = HttpRetrievalProvider(TEMPLATE)._normalize_payload(
        _provider_payload(_exact_length_timestamp()),
        TEMPLATE.replace("{query}", "example"),
    )
    assert result.status == "completed"
    assert result.sources[0]["observed_at"] == OBSERVED


@pytest.mark.parametrize("size", [65, 128, 100_000])
def test_http_retrieval_rejects_unbounded_timestamp(size):
    raw = OBSERVED + " " * (size - len(OBSERVED))
    result = HttpRetrievalProvider(TEMPLATE)._normalize_payload(
        _provider_payload(raw),
        TEMPLATE.replace("{query}", "example"),
    )
    assert result.status == "failed"
    assert result.reason == "invalid_source_observed_at"
    assert result.sources == ()


def test_provider_neutral_contract_rejects_oversized_timestamp():
    raw = OBSERVED + " " * (65 - len(OBSERVED))
    payload = _provider_payload(raw)
    assert validate_retrieved_evidence_bounds(payload["sources"], None) == (
        "invalid_source_observed_at"
    )
    with pytest.raises(ValueError, match="invalid_source_observed_at"):
        RetrievalProviderResponse(
            status="completed", sources=tuple(payload["sources"])
        )


def test_provider_neutral_normalizer_fails_closed_on_overlong_timestamp():
    raw = OBSERVED + " " * (65 - len(OBSERVED))
    result = RetrievalEvidenceNormalizer().normalize_result({
        "status": "completed",
        "sources": _provider_payload(raw)["sources"],
        "content": None,
    })
    assert result.status == "invalid_evidence"
    assert result.has_content is False
    assert result.content is None


def test_typed_source_observation_rejects_unbounded_time():
    with pytest.raises(ValueError, match="exceeds 64"):
        SourceObservation(
            "id-1",
            OBSERVED + " " * (65 - len(OBSERVED)),
            "submitted_evidence_observation",
        )


def test_canonical_observation_mapping_also_rejects_oversized_time():
    with pytest.raises(ValueError, match="exceeds 64"):
        SourceObservationResult.validate({
            "status": "usable",
            "source_count": 1,
            "observation_executed": True,
            "reason": None,
            "observations": [{
                "source_id": "id-1",
                "observed_at": OBSERVED + " " * (65 - len(OBSERVED)),
                "observation_method": "retrieval_provider_observation",
            }],
        })


@pytest.mark.parametrize("bad", [
    "2026-01-01T12:30:00",
    "not-a-time",
    "",
    " ",
    "2999-01-01T00:00:00Z",
])
def test_existing_timezone_format_and_future_safety_remains(bad):
    with pytest.raises(ValueError):
        normalize_reported_observation_time(bad)
    with pytest.raises(ValueError):
        SubmittedEvidenceBundle.from_mappings([_document(bad)])


def test_explicit_observation_freshness_stays_declared_and_stale():
    state = build_reality_state_from_evidence(
        "What is the current status of Company X?",
        [_document(OFFSET)],
        freshness_max_age_seconds=3600,
    )
    assert state["source_observation"]["observations"][0] == {
        "source_id": state["source_provenance"]["sources"][0]["source_id"],
        "observed_at": OBSERVED,
        "observation_method": "submitted_evidence_observation",
    }
    assert state["freshness"]["stale_count"] == 1
    assert state["freshness"]["fresh_count"] == 0
    assert state["status"] != "supported"
    assert state["claims"]["claim_count"] == 1
    assert state["claims"]["claims"][0]["source_refs"] == [URI]


def test_missing_time_without_policy_keeps_ingestion_not_fresh():
    doc = {"uri": URI, "content": "Company X is operational."}
    state = build_reality_state_from_evidence(
        "What is the current status of Company X?",
        [doc],
    )
    assert state["source_observation"]["observations"][0][
        "observation_method"
    ] == "submitted_evidence_ingestion"
    assert state["freshness"]["unknown_count"] == 1
    assert state["status"] != "supported"


def test_submitted_api_handler_preserves_timestamp_source_lineage():
    request = EvidenceRealityStateRequest(
        task="What is the current status of Company X?",
        documents=[_document(OFFSET)],
    )
    state = reality_state_from_evidence(request)
    assert state["source_observation"]["observations"][0][
        "observed_at"
    ] == OBSERVED
    assert state["evidence"]["sources"][0]["uri"] == URI
    assert state["claims"]["claims"][0]["source_refs"] == [URI]
    assert state["freshness"]["unknown_count"] == 1
