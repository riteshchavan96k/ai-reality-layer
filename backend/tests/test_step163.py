import pytest

from backend.app.reality.grounding_context import EvidenceGroundingContextBuilder
from backend.app.reality.grounding_context_contract import GroundingContext
from backend.app.reality.grounding_context_normalizer import GroundingContextNormalizer


def test_step163_accepts_canonical_grounding_context():
    context = GroundingContext.ready_result(
        task="Current weather",
        content="Observed information",
        sources=[{"title": "Source", "uri": "https://example.com"}],
    )

    assert GroundingContext.validate(context) is context
    assert context.source_count == 1


def test_step163_normalizes_mapping():
    context = GroundingContextNormalizer.normalize(
        {
            "status": "ready",
            "task": "Current weather",
            "content": "Observed information",
            "sources": [{"title": "Source", "uri": "https://example.com"}],
            "source_count": 1,
            "grounding_executed": True,
        }
    )

    assert isinstance(context, GroundingContext)
    assert context.status == "ready"
    assert context.source_count == 1


def test_step163_rejects_missing_required_field():
    with pytest.raises(ValueError, match="missing required fields"):
        GroundingContext.validate(
            {
                "status": "ready",
                "task": "Current weather",
                "content": "Observed information",
                "sources": [],
                "source_count": 0,
            }
        )


def test_step163_rejects_source_count_mismatch():
    with pytest.raises(ValueError, match="source_count must match sources"):
        GroundingContextNormalizer.normalize(
            {
                "status": "ready",
                "task": "Current weather",
                "content": "Observed information",
                "sources": [{"uri": "https://example.com"}],
                "source_count": 0,
                "grounding_executed": True,
            }
        )


def test_step163_rejects_unavailable_context_with_content():
    with pytest.raises(ValueError, match="not_available grounding context cannot contain content"):
        GroundingContextNormalizer.normalize(
            {
                "status": "not_available",
                "task": "Current weather",
                "content": "Unexpected content",
                "sources": [],
                "source_count": 0,
                "grounding_executed": True,
            }
        )


def test_step163_rejects_ready_context_without_execution():
    with pytest.raises(ValueError, match="ready grounding context must have grounding_executed=True"):
        GroundingContextNormalizer.normalize(
            {
                "status": "ready",
                "task": "Current weather",
                "content": None,
                "sources": [],
                "source_count": 0,
                "grounding_executed": False,
            }
        )


def test_step163_builder_routes_result_through_canonical_contract():
    result = EvidenceGroundingContextBuilder().build_result(
        "Current weather",
        {
            "status": "usable",
            "content": "Observed information",
            "sources": [{"title": "Source", "uri": "https://example.com"}],
        },
    )

    assert isinstance(result, GroundingContext)
    assert result.status == "ready"
    assert result.source_count == 1


def test_step163_builder_preserves_unavailable_semantics():
    result = EvidenceGroundingContextBuilder().build_result(
        "Current weather",
        {"status": "unavailable", "content": None, "sources": []},
    )

    assert result.status == "not_available"
    assert result.source_count == 0
    assert result.content is None
