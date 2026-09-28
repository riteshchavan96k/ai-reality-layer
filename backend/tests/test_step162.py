import pytest

from backend.app.reality.grounded_result import GroundedResultEnvelope, GroundedResultEnvelopeBuilder
from backend.app.reality.grounded_result_normalizer import GroundedResultEnvelopeNormalizer


def ready_context():
    return {
        "status": "ready",
        "source_count": 1,
        "sources": [{"title": "Example source", "uri": "https://example.com/source"}],
    }


def test_step162_accepts_canonical_grounded_result():
    result = GroundedResultEnvelope.validate(
        {
            "status": "ready",
            "grounded": True,
            "source_count": 1,
            "sources": [{"title": "Example source", "uri": "https://example.com/source"}],
        }
    )
    assert isinstance(result, GroundedResultEnvelope)
    assert result.grounded is True
    assert result.source_count == 1


def test_step162_normalizes_mapping():
    result = GroundedResultEnvelopeNormalizer.normalize(
        {
            "status": "not_available",
            "grounded": False,
            "source_count": 0,
            "sources": [],
        }
    )
    assert isinstance(result, GroundedResultEnvelope)
    assert result.status == "not_available"


def test_step162_rejects_missing_required_field():
    with pytest.raises(ValueError, match="missing required fields"):
        GroundedResultEnvelope.validate(
            {"status": "ready", "grounded": True, "source_count": 1}
        )


def test_step162_rejects_grounded_status_mismatch():
    with pytest.raises(ValueError, match="grounded must match status"):
        GroundedResultEnvelopeNormalizer.normalize(
            {
                "status": "not_available",
                "grounded": True,
                "source_count": 0,
                "sources": [],
            }
        )


def test_step162_rejects_source_count_mismatch():
    with pytest.raises(ValueError, match="source_count must match sources"):
        GroundedResultEnvelopeNormalizer.normalize(
            {
                "status": "ready",
                "grounded": True,
                "source_count": 2,
                "sources": [{"title": "Example", "uri": "https://example.com"}],
            }
        )


def test_step162_rejects_not_available_sources():
    with pytest.raises(ValueError, match="not_available envelope cannot contain sources"):
        GroundedResultEnvelopeNormalizer.normalize(
            {
                "status": "not_available",
                "grounded": False,
                "source_count": 1,
                "sources": [{"title": "Example", "uri": "https://example.com"}],
            }
        )


def test_step162_builder_returns_canonical_result():
    result = GroundedResultEnvelopeBuilder().build_result(ready_context(), {"answer": "ok"})
    assert isinstance(result, GroundedResultEnvelope)
    assert result.status == "ready"
    assert result.grounded is True
    assert result.source_count == 1


def test_step162_builder_preserves_not_available_state():
    result = GroundedResultEnvelopeBuilder().build_result(
        {"status": "not_available", "source_count": 0, "sources": []},
        None,
    )
    assert result.status == "not_available"
    assert result.grounded is False
    assert result.source_count == 0
