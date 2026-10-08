"""Step 203 — canonical retrieval-result consumption state integrity."""

import pytest

from backend.app.reality.evidence_normalizer import RetrievalEvidenceNormalizer
from backend.app.reality.retrieval_result import RetrievalResultContract
from backend.app.reality.retrieval_result_consumer import RetrievalResultConsumer
from backend.app.reality.retrieval_result_consumption import (
    RetrievalResultConsumption,
)
from backend.app.reality.retrieval_result_consumption_normalizer import (
    RetrievalResultConsumptionNormalizer,
)


REQUEST = {
    "query": "current status",
    "source_type": "live_web",
    "temporal_scope": "current",
    "required": True,
}
SOURCE = {"uri": "https://example.com"}
CONTENT = "The service is operational."


def _usable_mapping(
    *,
    retrieval_status: str = "completed",
    consumption_executed: object = True,
    reason: object = None,
) -> dict:
    return {
        "status": "usable",
        "retrieval_status": retrieval_status,
        "usable": True,
        "reason": reason,
        "consumption_executed": consumption_executed,
    }


def test_usable_consumption_rejects_false_execution_flag():
    with pytest.raises(
        ValueError,
        match="usable retrieval consumption requires consumption_executed to be True",
    ):
        RetrievalResultConsumption(
            status="usable",
            retrieval_status="completed",
            usable=True,
            consumption_executed=False,
        )


def test_mapping_rejects_usable_false_execution_flag():
    with pytest.raises(
        ValueError,
        match="usable retrieval consumption requires consumption_executed to be True",
    ):
        RetrievalResultConsumption.validate(
            _usable_mapping(consumption_executed=False)
        )


def test_normalizer_rejects_usable_false_execution_flag():
    with pytest.raises(
        ValueError,
        match="usable retrieval consumption requires consumption_executed to be True",
    ):
        RetrievalResultConsumptionNormalizer.normalize(
            _usable_mapping(consumption_executed=False)
        )


@pytest.mark.parametrize("retrieval_status", ["failed", "blocked"])
def test_usable_consumption_rejects_nonpositive_retrieval_status(retrieval_status):
    with pytest.raises(
        ValueError,
        match=(
            "usable retrieval consumption requires completed or not_required "
            "retrieval status"
        ),
    ):
        RetrievalResultConsumption.validate(
            _usable_mapping(retrieval_status=retrieval_status)
        )


def test_usable_helper_rejects_failed_retrieval_status():
    with pytest.raises(
        ValueError,
        match=(
            "usable retrieval consumption requires completed or not_required "
            "retrieval status"
        ),
    ):
        RetrievalResultConsumption.usable_result("failed")


def test_usable_helper_rejects_blocked_retrieval_status():
    with pytest.raises(
        ValueError,
        match=(
            "usable retrieval consumption requires completed or not_required "
            "retrieval status"
        ),
    ):
        RetrievalResultConsumption.usable_result("blocked")


def test_usable_consumption_rejects_reason():
    with pytest.raises(
        ValueError,
        match="usable retrieval consumption cannot contain a reason",
    ):
        RetrievalResultConsumption.validate(
            _usable_mapping(reason="unexpected_reason")
        )


def test_rejected_consumption_requires_nonempty_reason():
    with pytest.raises(
        ValueError,
        match="rejected retrieval consumption requires a nonempty reason",
    ):
        RetrievalResultConsumption(
            status="rejected",
            retrieval_status="failed",
            usable=False,
            reason=None,
            consumption_executed=True,
        )


def test_rejected_consumption_rejects_blank_reason():
    with pytest.raises(
        ValueError,
        match="rejected retrieval consumption requires a nonempty reason",
    ):
        RetrievalResultConsumption(
            status="rejected",
            retrieval_status="blocked",
            usable=False,
            reason="   ",
            consumption_executed=True,
        )


def test_rejected_consumption_may_record_not_executed():
    result = RetrievalResultConsumption(
        status="rejected",
        retrieval_status="blocked",
        usable=False,
        reason="consumption_not_executed",
        consumption_executed=False,
    )

    assert result.status == "rejected"
    assert result.usable is False
    assert result.reason == "consumption_not_executed"
    assert result.consumption_executed is False


def test_completed_usable_consumption_remains_valid():
    result = RetrievalResultConsumption.validate(
        _usable_mapping(retrieval_status="completed")
    )

    assert result.status == "usable"
    assert result.retrieval_status == "completed"
    assert result.usable is True
    assert result.reason is None
    assert result.consumption_executed is True


def test_not_required_usable_consumption_remains_valid():
    result = RetrievalResultConsumption.validate(
        _usable_mapping(retrieval_status="not_required")
    )

    assert result.status == "usable"
    assert result.retrieval_status == "not_required"
    assert result.usable is True
    assert result.reason is None
    assert result.consumption_executed is True


def test_non_boolean_execution_flag_remains_rejected():
    with pytest.raises(
        ValueError,
        match="consumption_executed must be a boolean",
    ):
        RetrievalResultConsumption.validate(
            _usable_mapping(consumption_executed=1)
        )


def test_existing_status_usability_integrity_remains_intact():
    with pytest.raises(
        ValueError,
        match="usable status requires usable=True",
    ):
        RetrievalResultConsumption(
            status="usable",
            retrieval_status="completed",
            usable=False,
            consumption_executed=True,
        )


def test_production_consumer_completed_path_is_executed_usable():
    retrieval = RetrievalResultContract.completed(
        REQUEST,
        "test-provider",
        [SOURCE],
        CONTENT,
    )

    result = RetrievalResultConsumer().consume(retrieval)

    assert result.status == "usable"
    assert result.retrieval_status == "completed"
    assert result.usable is True
    assert result.reason is None
    assert result.consumption_executed is True


def test_production_consumer_not_required_path_is_executed_usable():
    request = {**REQUEST, "required": False}
    retrieval = RetrievalResultContract.not_required(request)

    result = RetrievalResultConsumer().consume(retrieval)

    assert result.status == "usable"
    assert result.retrieval_status == "not_required"
    assert result.usable is True
    assert result.reason is None
    assert result.consumption_executed is True


def test_production_consumer_failed_path_is_rejected_with_reason():
    retrieval = RetrievalResultContract.failed(
        REQUEST,
        "test-provider",
        "provider_error",
    )

    result = RetrievalResultConsumer().consume(retrieval)

    assert result.status == "rejected"
    assert result.retrieval_status == "failed"
    assert result.usable is False
    assert result.reason == "provider_error"
    assert result.consumption_executed is True


def test_production_consumer_blocked_path_is_rejected_with_reason():
    retrieval = RetrievalResultContract.blocked(
        REQUEST,
        None,
        "provider_unavailable",
    )

    result = RetrievalResultConsumer().consume(retrieval)

    assert result.status == "rejected"
    assert result.retrieval_status == "blocked"
    assert result.usable is False
    assert result.reason == "provider_unavailable"
    assert result.consumption_executed is True


def test_production_consumer_empty_completed_path_is_rejected_with_reason():
    retrieval = RetrievalResultContract.completed(
        REQUEST,
        "test-provider",
        [],
        None,
    )

    result = RetrievalResultConsumer().consume(retrieval)

    assert result.status == "rejected"
    assert result.retrieval_status == "completed"
    assert result.usable is False
    assert result.reason == "empty_retrieval_result"
    assert result.consumption_executed is True


def test_valid_completed_consumption_remains_compatible_with_step202_normalization():
    retrieval = RetrievalResultContract.completed(
        REQUEST,
        "test-provider",
        [SOURCE],
        CONTENT,
    )
    consumption = RetrievalResultConsumer().consume(retrieval)

    assert consumption.status == "usable"
    assert consumption.consumption_executed is True

    evidence = RetrievalEvidenceNormalizer().normalize_result(retrieval)

    assert evidence.status == "completed"
    assert evidence.normalization_executed is True


def test_not_required_consumption_remains_compatible_with_normalization():
    request = {**REQUEST, "required": False}
    retrieval = RetrievalResultContract.not_required(request)
    consumption = RetrievalResultConsumer().consume(retrieval)

    assert consumption.status == "usable"
    assert consumption.retrieval_status == "not_required"

    evidence = RetrievalEvidenceNormalizer().normalize_result(retrieval)

    assert evidence.status == "not_required"
    assert evidence.normalization_executed is True


def test_rejected_helper_remains_valid():
    result = RetrievalResultConsumption.rejected_result(
        "blocked",
        "retrieval_provider_unavailable",
    )

    assert result.status == "rejected"
    assert result.usable is False
    assert result.reason == "retrieval_provider_unavailable"
    assert result.consumption_executed is True
