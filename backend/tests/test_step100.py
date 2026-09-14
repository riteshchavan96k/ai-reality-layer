import pytest

from backend.app.reality.grounding_execution_context import GroundingExecutionContext
from backend.app.reality.grounding_execution_context_normalizer import GroundingExecutionContextNormalizer


def test_typed_execution_context_is_preserved() -> None:
    context = GroundingExecutionContext.ready_result(
        "Check the current evidence",
        "Verified evidence",
        [{"title": "Source A", "url": "https://example.com/a"}],
    )
    assert GroundingExecutionContextNormalizer.normalize(context) is context


def test_ready_mapping_is_normalized() -> None:
    result = GroundingExecutionContextNormalizer.normalize(
        {
            "task": "Check the current evidence",
            "grounding_status": "ready",
            "content": "Verified evidence",
            "sources": [{"title": "Source A"}],
            "source_count": 1,
        }
    )
    assert isinstance(result, GroundingExecutionContext)
    assert result.grounding_status == "ready"
    assert result.source_count == 1
    assert result.execution_allowed is True


def test_not_available_mapping_is_normalized() -> None:
    result = GroundingExecutionContextNormalizer.normalize(
        {
            "task": "Explain a general concept",
            "grounding_status": "not_available",
            "content": None,
            "sources": [],
            "source_count": 0,
        }
    )
    assert result.grounding_status == "not_available"
    assert result.content is None
    assert result.sources == []


def test_mapping_preserves_explicit_execution_permission() -> None:
    result = GroundingExecutionContextNormalizer.normalize(
        {
            "task": "Check evidence",
            "grounding_status": "ready",
            "content": "Evidence",
            "sources": [],
            "source_count": 0,
            "execution_allowed": False,
            "context_prepared": True,
        }
    )
    assert result.execution_allowed is False
    assert result.context_prepared is True


def test_mapping_preserves_explicit_preparation_state() -> None:
    result = GroundingExecutionContextNormalizer.normalize(
        {
            "task": "Check evidence",
            "grounding_status": "ready",
            "content": None,
            "sources": [],
            "source_count": 0,
            "context_prepared": False,
        }
    )
    assert result.context_prepared is False


def test_unsupported_shape_is_rejected() -> None:
    with pytest.raises(ValueError, match="must be a result contract or mapping"):
        GroundingExecutionContextNormalizer.normalize("invalid")


def test_invalid_source_shape_is_rejected() -> None:
    with pytest.raises(ValueError, match="sources must be a list"):
        GroundingExecutionContextNormalizer.normalize(
            {
                "task": "Check",
                "grounding_status": "ready",
                "content": "Evidence",
                "sources": "invalid",
                "source_count": 0,
            }
        )


def test_invalid_nested_source_shape_is_rejected() -> None:
    with pytest.raises(ValueError, match="sources must be dictionaries"):
        GroundingExecutionContextNormalizer.normalize(
            {
                "task": "Check",
                "grounding_status": "ready",
                "content": "Evidence",
                "sources": ["invalid"],
                "source_count": 1,
            }
        )


def test_canonical_contract_rejects_inconsistent_mapping() -> None:
    with pytest.raises(ValueError, match="source_count must match sources"):
        GroundingExecutionContextNormalizer.normalize(
            {
                "task": "Check",
                "grounding_status": "ready",
                "content": "Evidence",
                "sources": [{"title": "A"}],
                "source_count": 0,
            }
        )


def test_deterministic_serialization_after_normalization() -> None:
    result = GroundingExecutionContextNormalizer.normalize(
        {
            "task": "Check",
            "grounding_status": "ready",
            "content": "Evidence",
            "sources": [{"title": "A", "url": "https://example.com/a"}],
            "source_count": 1,
        }
    )
    assert result.to_dict() == {
        "task": "Check",
        "grounding_status": "ready",
        "content": "Evidence",
        "sources": [{"title": "A", "url": "https://example.com/a"}],
        "source_count": 1,
        "execution_allowed": True,
        "context_prepared": True,
    }
