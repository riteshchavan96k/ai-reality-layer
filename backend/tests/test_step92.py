import pytest

from backend.app.reality.grounding_context import EvidenceGroundingContextBuilder
from backend.app.reality.grounding_context_contract import GroundingContext


def test_ready_context_uses_canonical_contract() -> None:
    result = EvidenceGroundingContextBuilder().build_result(
        "What happened today?",
        {
            "status": "usable",
            "sources": [{"title": "Source A", "uri": "https://example.com/a"}],
            "content": "Evidence content",
        },
    )
    assert isinstance(result, GroundingContext)
    assert result.status == "ready"
    assert result.source_count == 1
    assert result.grounding_executed is True


def test_not_available_context_is_explicit() -> None:
    result = EvidenceGroundingContextBuilder().build_result(
        "Explain this",
        {"status": "insufficient", "sources": [], "content": None},
    )
    assert result.status == "not_available"
    assert result.content is None
    assert result.sources == []
    assert result.source_count == 0


def test_legacy_build_api_serializes_canonical_contract() -> None:
    result = EvidenceGroundingContextBuilder().build(
        "Current information",
        {
            "status": "usable",
            "sources": [{"title": "Source", "uri": "https://example.com"}],
            "content": "Content",
        },
    )
    assert result == {
        "status": "ready",
        "task": "Current information",
        "content": "Content",
        "sources": [{"title": "Source", "uri": "https://example.com"}],
        "source_count": 1,
        "grounding_executed": True,
    }


def test_source_count_must_match_sources() -> None:
    with pytest.raises(ValueError, match="source_count must match sources"):
        GroundingContext(
            status="ready",
            task="Task",
            content="Content",
            sources=[{"title": "A", "uri": "u"}],
            source_count=0,
        )


def test_not_available_cannot_contain_evidence() -> None:
    with pytest.raises(ValueError, match="cannot contain sources"):
        GroundingContext(
            status="not_available",
            task="Task",
            content=None,
            sources=[{"title": "A", "uri": "u"}],
            source_count=1,
        )


def test_invalid_status_is_rejected() -> None:
    with pytest.raises(ValueError, match="status must be ready or not_available"):
        GroundingContext(
            status="invalid",
            task="Task",
            content=None,
            sources=[],
            source_count=0,
        )


def test_serialization_is_deterministic() -> None:
    result = GroundingContext.ready_result(
        "Task",
        "Content",
        [{"title": "A", "uri": "u"}],
    )
    assert result.to_dict() == {
        "status": "ready",
        "task": "Task",
        "content": "Content",
        "sources": [{"title": "A", "uri": "u"}],
        "source_count": 1,
        "grounding_executed": True,
    }
