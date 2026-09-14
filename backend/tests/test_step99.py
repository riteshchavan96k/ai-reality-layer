import pytest

from backend.app.reality.grounding_execution_context import GroundingExecutionContext


def test_ready_context_preserves_task_content_and_sources() -> None:
    context = GroundingExecutionContext.ready_result(
        "What is the current status?",
        "Current status is verified.",
        [{"title": "Source A", "url": "https://example.com/a"}],
    )
    assert context.grounding_status == "ready"
    assert context.task == "What is the current status?"
    assert context.content == "Current status is verified."
    assert context.source_count == 1
    assert context.execution_allowed is True
    assert context.context_prepared is True


def test_not_available_context_is_explicitly_empty() -> None:
    context = GroundingExecutionContext.not_available_result("Explain the concept")
    assert context.grounding_status == "not_available"
    assert context.content is None
    assert context.sources == []
    assert context.source_count == 0
    assert context.execution_allowed is True


def test_from_grounding_normalizes_source_copies() -> None:
    source = {"title": "Source A", "url": "https://example.com/a"}
    context = GroundingExecutionContext.from_grounding(
        {
            "status": "ready",
            "task": "Check the evidence",
            "content": "Evidence",
            "sources": [source],
            "source_count": 1,
        }
    )
    assert context.to_dict()["sources"] == [source]
    assert context.to_dict()["grounding_status"] == "ready"


def test_from_grounding_can_record_execution_gate_decision() -> None:
    context = GroundingExecutionContext.from_grounding(
        {
            "status": "ready",
            "task": "Check the evidence",
            "content": "Evidence",
            "sources": [],
            "source_count": 0,
        },
        execution_allowed=False,
    )
    assert context.execution_allowed is False


def test_source_count_must_match_sources() -> None:
    with pytest.raises(ValueError, match="source_count must match sources"):
        GroundingExecutionContext(
            task="Check",
            grounding_status="ready",
            content="Evidence",
            sources=[{"title": "A"}],
            source_count=0,
        )


def test_not_available_context_cannot_contain_evidence() -> None:
    with pytest.raises(ValueError, match="not_available execution context cannot contain content"):
        GroundingExecutionContext(
            task="Check",
            grounding_status="not_available",
            content="Unexpected evidence",
            sources=[],
            source_count=0,
        )


def test_invalid_grounding_status_is_rejected() -> None:
    with pytest.raises(ValueError, match="grounding_status must be ready or not_available"):
        GroundingExecutionContext(
            task="Check",
            grounding_status="unknown",
            content=None,
            sources=[],
            source_count=0,
        )


def test_invalid_execution_allowed_type_is_rejected() -> None:
    with pytest.raises(ValueError, match="execution_allowed must be a boolean"):
        GroundingExecutionContext(
            task="Check",
            grounding_status="ready",
            content=None,
            sources=[],
            source_count=0,
            execution_allowed="yes",  # type: ignore[arg-type]
        )


def test_deterministic_serialization() -> None:
    context = GroundingExecutionContext.ready_result(
        "Check",
        "Evidence",
        [{"title": "A", "url": "https://example.com/a"}],
    )
    assert context.to_dict() == {
        "task": "Check",
        "grounding_status": "ready",
        "content": "Evidence",
        "sources": [{"title": "A", "url": "https://example.com/a"}],
        "source_count": 1,
        "execution_allowed": True,
        "context_prepared": True,
    }
