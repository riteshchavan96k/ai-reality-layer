import pytest

from backend.app.reality.grounding_context_contract import GroundingContext
from backend.app.reality.grounding_context_normalizer import GroundingContextNormalizer


def test_typed_context_is_preserved() -> None:
    context = GroundingContext.ready_result("Task", "Content", [{"title": "A", "uri": "u"}])
    assert GroundingContextNormalizer.normalize(context) is context


def test_ready_mapping_is_normalized() -> None:
    context = GroundingContextNormalizer.normalize(
        {
            "status": "ready",
            "task": "Task",
            "content": "Content",
            "sources": [{"title": "A", "uri": "u"}],
            "source_count": 1,
        }
    )
    assert isinstance(context, GroundingContext)
    assert context.status == "ready"
    assert context.grounding_executed is True


def test_unavailable_mapping_is_normalized() -> None:
    context = GroundingContextNormalizer.normalize(
        {
            "status": "not_available",
            "task": "Task",
            "content": None,
            "sources": [],
            "source_count": 0,
            "grounding_executed": False,
        }
    )
    assert context.status == "not_available"
    assert context.grounding_executed is False


def test_invalid_shape_is_rejected() -> None:
    with pytest.raises(ValueError, match="grounding context must be a result contract or mapping"):
        GroundingContextNormalizer.normalize(None)


def test_invalid_source_shape_is_rejected() -> None:
    with pytest.raises(ValueError, match="each grounding source must be a mapping"):
        GroundingContextNormalizer.normalize(
            {
                "status": "ready",
                "task": "Task",
                "content": "Content",
                "sources": ["invalid"],
                "source_count": 1,
            }
        )


def test_inconsistent_mapping_is_rejected_by_contract() -> None:
    with pytest.raises(ValueError, match="source_count must match sources"):
        GroundingContextNormalizer.normalize(
            {
                "status": "ready",
                "task": "Task",
                "content": "Content",
                "sources": [{"title": "A", "uri": "u"}],
                "source_count": 0,
            }
        )


def test_serialization_is_deterministic() -> None:
    context = GroundingContextNormalizer.normalize(
        {
            "status": "ready",
            "task": "Task",
            "content": "Content",
            "sources": [{"title": "A", "uri": "u"}],
            "source_count": 1,
            "grounding_executed": True,
        }
    )
    assert context.to_dict() == {
        "status": "ready",
        "task": "Task",
        "content": "Content",
        "sources": [{"title": "A", "uri": "u"}],
        "source_count": 1,
        "grounding_executed": True,
    }
