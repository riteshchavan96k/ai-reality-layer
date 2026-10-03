from datetime import datetime, timezone

import pytest

from backend.app.reality.source_observation import SourceObservation, SourceObservationResult
from backend.app.reality.source_observation_builder import SourceObservationBuilder
from backend.app.reality.source_provenance import SourceProvenance, SourceProvenanceResult


def provenance():
    source = SourceProvenance("id-1", "https://example.com", "https://example.com", "Example")
    return SourceProvenanceResult.usable_result((source,))


def test_observation_is_immutable_and_serializable():
    item = SourceObservation("id-1", "2026-09-18T12:00:00Z")
    assert item.to_dict() == {
        "source_id": "id-1",
        "observed_at": "2026-09-18T12:00:00Z",
        "observation_method": "retrieval_observation",
    }
    with pytest.raises(Exception):
        item.source_id = "changed"


def test_builder_uses_injected_clock_deterministically():
    clock = lambda: datetime(2026, 9, 18, 12, 0, tzinfo=timezone.utc)
    result = SourceObservationBuilder(clock=clock).build_result(provenance())
    assert result.status == "usable"
    assert result.observations[0].observed_at == "2026-09-18T12:00:00Z"
    assert result.observations[0].source_id == "id-1"


def test_builder_creates_one_observation_per_source():
    p = SourceProvenanceResult.usable_result(
        (
            SourceProvenance("a", "https://a.example", "https://a.example"),
            SourceProvenance("b", "https://b.example", "https://b.example"),
        )
    )
    result = SourceObservationBuilder(clock=lambda: datetime(2026, 9, 18, 12, 0, tzinfo=timezone.utc)).build_result(p)
    assert result.source_count == 2


def test_unavailable_and_empty_provenance_fail_closed():
    unavailable = SourceProvenanceResult.unavailable_result("no_provenance")
    empty = SourceProvenanceResult.empty_result()
    builder = SourceObservationBuilder(clock=lambda: datetime(2026, 9, 18, 12, 0, tzinfo=timezone.utc))
    assert builder.build_result(unavailable).status == "unavailable"
    assert builder.build_result(empty).status == "empty"


def test_builder_rejects_naive_clock():
    with pytest.raises(ValueError, match="timezone-aware"):
        SourceObservationBuilder(clock=lambda: datetime(2026, 9, 18, 12, 0)).build_result(provenance())


def test_observation_rejects_future_timestamp():
    with pytest.raises(ValueError, match="future"):
        SourceObservation("id", "2999-01-01T00:00:00Z")


def test_observation_rejects_timestamp_without_timezone():
    with pytest.raises(ValueError, match="timezone"):
        SourceObservation("id", "2026-09-18T12:00:00")


def test_result_rejects_inconsistent_states():
    item = SourceObservation("id", "2026-09-18T12:00:00Z")
    with pytest.raises(ValueError, match="usable source observation requires"):
        SourceObservationResult("usable")
    with pytest.raises(ValueError, match="empty source observation cannot"):
        SourceObservationResult("empty", observations=(item,), source_count=1)
    with pytest.raises(ValueError, match="requires a reason"):
        SourceObservationResult("unavailable")
