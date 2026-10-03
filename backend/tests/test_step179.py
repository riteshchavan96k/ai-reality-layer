import json

from backend.app.orchestrator.orchestrator import build_reality_state
from backend.app.reality.claim_evidence_linker import ClaimEvidenceLinker
from backend.app.reality.claim_extraction import ClaimExtractionResult, EvidenceClaim
from backend.app.reality.confidence_signal_aggregator import (
    RealityConfidenceSignalAggregator,
)
from backend.app.reality.retrieval_result import RetrievalResultContract
from backend.app.reality.source_provenance_builder import SourceProvenanceBuilder


def _completed_evidence():
    return {
        "status": "completed",
        "sources": [
            {
                "title": "Company X update",
                "uri": "https://example.test/company-x",
            }
        ],
        "content": "Company X launched Feature A today.",
        "source_count": 1,
        "has_content": True,
        "normalization_executed": True,
    }


def _claim_result():
    return ClaimExtractionResult.usable_result(
        (
            EvidenceClaim(
                "Company X launched Feature A today.",
                ("https://example.test/company-x",),
            ),
        ),
        source_count=1,
    )


def test_claim_linker_accepts_canonical_completed_evidence():
    result = ClaimEvidenceLinker().link_result(
        _claim_result(),
        _completed_evidence(),
    )

    assert result.status == "usable"
    assert result.claim_count == 1
    assert result.linked_claim_count == 1
    assert result.unlinked_claim_count == 0
    assert result.links[0].source_ref == "https://example.test/company-x"


def test_claim_linker_preserves_legacy_usable_alias():
    evidence = _completed_evidence()
    evidence["status"] = "usable"

    result = ClaimEvidenceLinker().link_result(
        _claim_result(),
        evidence,
    )

    assert result.status == "usable"
    assert result.linked_claim_count == 1


def test_source_provenance_accepts_canonical_completed_evidence():
    result = SourceProvenanceBuilder().build_result(
        _completed_evidence()
    )

    assert result.status == "usable"
    assert result.source_count == 1
    assert result.sources[0].source_ref == "https://example.test/company-x"
    assert len(result.sources[0].source_id) == 64


def test_source_provenance_preserves_legacy_usable_alias():
    evidence = _completed_evidence()
    evidence["status"] = "usable"

    result = SourceProvenanceBuilder().build_result(evidence)

    assert result.status == "usable"
    assert result.source_count == 1


def test_unknown_freshness_forces_uncertain_reality_confidence():
    result = RealityConfidenceSignalAggregator().aggregate_result(
        evidence_quality={"status": "usable"},
        linking={
            "status": "usable",
            "claim_count": 1,
            "linked_claim_count": 1,
        },
        freshness={
            "status": "usable",
            "stale_count": 0,
            "unknown_count": 1,
        },
        conflicts={
            "status": "empty",
            "conflict_count": 0,
        },
    )

    assert result.status == "uncertain"
    assert result.claim_coverage == 1.0
    assert "freshness_uncertain" in result.signals


def test_fully_linked_known_fresh_evidence_can_remain_supported():
    result = RealityConfidenceSignalAggregator().aggregate_result(
        evidence_quality={"status": "usable"},
        linking={
            "status": "usable",
            "claim_count": 1,
            "linked_claim_count": 1,
        },
        freshness={
            "status": "usable",
            "stale_count": 0,
            "unknown_count": 0,
        },
        conflicts={
            "status": "empty",
            "conflict_count": 0,
        },
    )

    assert result.status == "supported"
    assert "sources_within_declared_observation_window" in result.signals


class _CompletedRetrievalEngine:
    def retrieve(self, contract):
        return RetrievalResultContract.completed(
            contract["request"],
            provider="test-provider",
            sources=[
                {
                    "title": "Company X update",
                    "uri": "https://example.test/company-x",
                }
            ],
            content=(
                "Company X launched Feature A today. "
                "Company X continues to operate."
            ),
        )


def test_completed_retrieval_builds_linked_provenance_backed_reality_state():
    state = build_reality_state(
        "What is the current status of Company X?",
        retrieval_engine=_CompletedRetrievalEngine(),
    )

    assert state["status"] == "uncertain"
    assert state["evidence"]["status"] == "completed"

    assert state["claims"]["status"] == "usable"
    assert state["claims"]["claim_count"] == 2

    linking = state["claim_evidence_linking"]
    assert linking["status"] == "usable"
    assert linking["claim_count"] == 2
    assert linking["linked_claim_count"] == 2
    assert linking["unlinked_claim_count"] == 0

    provenance = state["source_provenance"]
    assert provenance["status"] == "usable"
    assert provenance["source_count"] == 1

    observation = state["source_observation"]
    assert observation["status"] == "usable"
    assert observation["source_count"] == 1

    freshness = state["freshness"]
    assert freshness["status"] == "usable"
    assert freshness["unknown_count"] == 1

    confidence = state["confidence_signals"]
    assert confidence["status"] == "uncertain"
    assert confidence["claim_coverage"] == 1.0
    assert "freshness_uncertain" in confidence["signals"]


class _HttpResponse:
    def __init__(self, payload):
        self._payload = json.dumps(payload).encode("utf-8")

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc, tb):
        return False

    def read(self, size=-1):
        return self._payload[:size] if size >= 0 else self._payload


def test_configured_http_retrieval_reaches_reality_state(
    monkeypatch,
):
    payload = {
        "status": "completed",
        "content": "Company X launched Feature A today.",
        "sources": [
            {
                "title": "Official Company X update",
                "uri": "https://example.test/company-x",
            }
        ],
    }

    def fake_open(request, timeout):
        assert request.full_url.startswith(
            "https://retrieval.example.test/search?q="
        )
        assert timeout == 10.0
        return _HttpResponse(payload)

    monkeypatch.setenv(
        "ARL_HTTP_RETRIEVAL_ENDPOINT_TEMPLATE",
        "https://retrieval.example.test/search?q={query}",
    )
    monkeypatch.setattr(
        "backend.app.reality.http_retrieval_provider.urlopen",
        fake_open,
    )

    state = build_reality_state(
        "What is the current status of Company X?"
    )

    assert state["status"] == "uncertain"
    assert state["evidence"]["status"] == "completed"
    assert state["claims"]["status"] == "usable"
    assert state["claim_evidence_linking"]["status"] == "usable"
    assert state["claim_evidence_linking"]["linked_claim_count"] == 1
    assert state["source_provenance"]["status"] == "usable"
    assert state["source_observation"]["status"] == "usable"
    assert state["freshness"]["unknown_count"] == 1
    assert state["confidence_signals"]["status"] == "uncertain"
