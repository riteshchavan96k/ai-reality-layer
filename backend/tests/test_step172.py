from copy import deepcopy

import pytest

from backend.app.orchestrator.orchestrator import orchestrate_task
from backend.app.orchestrator.result_contract import OrchestrationResult
from backend.app.orchestrator.result_normalizer import (
    OrchestrationResultNormalizer,
)


_TIMESTAMP = "2026-10-01T00:00:00+00:00"
_FINGERPRINT = "a" * 64


def _trace():
    return [
        {
            "stage": "test",
            "status": "completed",
            "timestamp": _TIMESTAMP,
        }
    ]


def _common():
    return {
        "analysis": {},
        "routing": {},
        "approval": {},
        "trace": _trace(),
    }


def _full_execution(
    model="model-a",
    *,
    attempts=1,
    total_attempts=1,
    budget_limit=3,
    fallback_used=False,
):
    return {
        "status": "success",
        "model": model,
        "attempts": attempts,
        "total_attempts": total_attempts,
        "budget_limit": budget_limit,
        "attempts_by_model": {model: total_attempts},
        "fallback_used": fallback_used,
        "result": {
            "text": "answer",
            "model": model,
            "provider": "test-provider",
        },
        "errors": None,
    }


def _execution_summary(execution):
    return {
        "status": execution["status"],
        "model": execution["model"],
        "attempts": execution["attempts"],
        "total_attempts": execution["total_attempts"],
        "budget_limit": execution["budget_limit"],
        "attempts_by_model": dict(execution["attempts_by_model"]),
        "fallback_used": execution["fallback_used"],
    }


def _evaluation(score=0.9, status="pass"):
    return {
        "score": score,
        "status": status,
        "custom_signal": "step172",
    }


def _recovery(execution, evaluation):
    return {
        "used": False,
        "reason": "initial_evaluation_passed",
        "improved": False,
        "best": {
            "model": execution["model"],
            "execution": deepcopy(execution),
            "evaluation": deepcopy(evaluation),
        },
        "recovery_attempts": 0,
        "candidates_tried": [],
    }


def _outcome(
    *,
    model="model-a",
    execution_status="success",
    evaluation_score=0.9,
    attempts=1,
    total_attempts=1,
    budget_limit=3,
    fallback_used=False,
):
    return {
        "record_id": 1,
        "task_fingerprint": _FINGERPRINT,
        "task_type": "general",
        "routed_model": "model-a",
        "executed_model": model if execution_status == "success" else None,
        "execution_status": execution_status,
        "evaluation_score": evaluation_score,
        "attempts": attempts,
        "total_attempts": total_attempts,
        "budget_limit": budget_limit,
        "fallback_used": fallback_used,
        "timestamp": _TIMESTAMP,
    }


def _grounded_result():
    return {
        "status": "not_available",
        "grounded": False,
        "source_count": 0,
        "sources": [],
    }


def _success_result():
    execution = _full_execution()
    evaluation = _evaluation()
    return {
        "status": "orchestrated",
        **_common(),
        "execution": _execution_summary(execution),
        "result": deepcopy(execution["result"]),
        "grounding": _grounded_result(),
        "evaluation": evaluation,
        "quality_recovery": _recovery(execution, evaluation),
        "outcome": _outcome(),
        "extension": {"source": "step172"},
    }


@pytest.mark.parametrize(
    "raw",
    [
        {
            "status": "awaiting_human_approval",
            **_common(),
        },
        {
            "status": "retrieval_unavailable",
            **_common(),
            "retrieval": {},
            "evidence": {},
            "evidence_quality": {},
            "grounding": _grounded_result(),
        },
        {
            "status": "grounding_unavailable",
            **_common(),
            "retrieval": {},
            "evidence": {},
            "evidence_quality": {},
            "grounding": {"status": "not_available"},
        },
        {
            "status": "execution_context_unavailable",
            **_common(),
            "retrieval": {},
            "evidence": {},
            "evidence_quality": {},
            "grounding": {"status": "ready"},
            "execution_context": {},
        },
    ],
)
def test_non_execution_terminal_statuses_are_canonical(raw):
    result = OrchestrationResultNormalizer.normalize(raw)

    assert isinstance(result, OrchestrationResult)
    assert result.to_dict()["status"] == raw["status"]
    assert result.to_dict()["trace"][0]["stage"] == "test"


def test_execution_failed_terminal_status_validates_execution_and_outcome():
    raw = {
        "status": "execution_failed",
        **_common(),
        "execution": {
            "status": "failed",
            "model": None,
            "attempts": 1,
            "total_attempts": 1,
            "budget_limit": 3,
            "attempts_by_model": {"model-a": 1},
            "fallback_used": False,
            "result": None,
            "errors": {"model-a": "provider_execution_failed"},
        },
        "outcome": _outcome(
            execution_status="failed",
            evaluation_score=None,
        ),
    }

    result = OrchestrationResultNormalizer.normalize(raw).to_dict()

    assert result["status"] == "execution_failed"
    assert result["execution"]["status"] == "failed"
    assert result["outcome"]["execution_status"] == "failed"


def test_success_result_is_canonical_and_preserves_extensions():
    raw = _success_result()

    result = OrchestrationResultNormalizer.normalize(raw).to_dict()

    assert result["status"] == "orchestrated"
    assert result["execution"]["model"] == "model-a"
    assert result["evaluation"]["score"] == 0.9
    assert result["quality_recovery"]["best"]["model"] == "model-a"
    assert result["outcome"]["executed_model"] == "model-a"
    assert result["extension"] == {"source": "step172"}


def test_unknown_terminal_status_is_rejected():
    with pytest.raises(
        ValueError,
        match="status must be a supported orchestration terminal status",
    ):
        OrchestrationResultNormalizer.normalize(
            {
                "status": "unknown",
                **_common(),
            }
        )


def test_missing_status_specific_field_is_rejected():
    raw = {
        "status": "orchestrated",
        **_common(),
    }

    with pytest.raises(
        ValueError,
        match="orchestrated orchestration result missing fields",
    ):
        OrchestrationResultNormalizer.normalize(raw)


def test_invalid_trace_is_rejected_at_public_result_boundary():
    raw = {
        "status": "awaiting_human_approval",
        **_common(),
        "trace": [
            {
                "stage": "test",
                "status": "completed",
                "timestamp": "not-a-timestamp",
            }
        ],
    }

    with pytest.raises(ValueError, match="valid ISO-8601 timestamp"):
        OrchestrationResultNormalizer.normalize(raw)


def test_success_rejects_recovery_model_mismatch():
    raw = _success_result()
    raw["quality_recovery"]["best"]["model"] = "model-b"
    raw["quality_recovery"]["best"]["execution"]["model"] = "model-b"
    raw["quality_recovery"]["best"]["execution"]["result"]["model"] = "model-b"

    with pytest.raises(
        ValueError,
        match="quality recovery best model must match orchestration execution model",
    ):
        OrchestrationResultNormalizer.normalize(raw)


def test_success_rejects_recovery_execution_attempt_mismatch():
    raw = _success_result()
    recovery_execution = raw["quality_recovery"]["best"]["execution"]
    recovery_execution["total_attempts"] = 2
    recovery_execution["attempts_by_model"] = {"model-a": 2}

    with pytest.raises(
        ValueError,
        match="quality recovery execution total_attempts must match",
    ):
        OrchestrationResultNormalizer.normalize(raw)


def test_success_rejects_selected_evaluation_mismatch():
    raw = _success_result()
    raw["quality_recovery"]["best"]["evaluation"]["score"] = 0.8

    with pytest.raises(
        ValueError,
        match="quality recovery best evaluation must match orchestration evaluation",
    ):
        OrchestrationResultNormalizer.normalize(raw)


def test_success_rejects_outcome_model_mismatch():
    raw = _success_result()
    raw["outcome"]["executed_model"] = "model-b"

    with pytest.raises(
        ValueError,
        match="outcome executed_model must match orchestration execution model",
    ):
        OrchestrationResultNormalizer.normalize(raw)


def test_success_rejects_outcome_attempt_mismatch():
    raw = _success_result()
    raw["outcome"]["total_attempts"] = 2

    with pytest.raises(
        ValueError,
        match="outcome total_attempts must match orchestration execution total_attempts",
    ):
        OrchestrationResultNormalizer.normalize(raw)


def test_success_rejects_result_model_mismatch():
    raw = _success_result()
    raw["result"]["model"] = "model-b"

    with pytest.raises(
        ValueError,
        match="result model must match orchestration execution model",
    ):
        OrchestrationResultNormalizer.normalize(raw)


def test_public_orchestrator_returns_canonical_public_result():
    result = orchestrate_task("Tell me about artificial intelligence")

    normalized = OrchestrationResultNormalizer.normalize(result).to_dict()

    assert normalized == result
    assert result["status"] in {
        "awaiting_human_approval",
        "retrieval_unavailable",
        "grounding_unavailable",
        "execution_context_unavailable",
        "execution_failed",
        "orchestrated",
    }
