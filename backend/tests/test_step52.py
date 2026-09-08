import pytest

from backend.app.models.provider_execution_result import ProviderExecutionResultContract
from backend.app.models.provider_invocation_executor import ProviderInvocationExecutor


class FakeAdapter:
    def __init__(self, result=None, error=None):
        self.result = result or {
            "text": "normalized response",
            "model": "fake-model",
            "provider": "fake-provider",
        }
        self.error = error
        self.calls = 0

    def generate(self, task, context=None):
        self.calls += 1
        if self.error is not None:
            raise self.error
        return self.result


def test_completed_result_uses_model_response_contract():
    contract = ProviderExecutionResultContract()
    result = contract.normalize(
        {
            "status": "completed",
            "execution_performed": True,
            "request": {"provider_name": "fake-provider"},
            "result": {"text": "answer", "provider": "fake-provider"},
        },
        "fake-model",
    )

    assert result["status"] == "completed"
    assert result["execution_performed"] is True
    assert result["result"] == {
        "text": "answer",
        "model": "fake-model",
        "provider": "fake-provider",
    }


def test_completed_result_preserves_grounding_metadata():
    contract = ProviderExecutionResultContract()
    result = contract.normalize(
        {
            "status": "completed",
            "execution_performed": True,
            "request": {},
            "result": {
                "text": "grounded answer",
                "provider": "fake-provider",
                "grounding": {"grounded": True, "source_count": 2},
            },
        },
        "fake-model",
    )

    assert result["result"]["grounding"] == {"grounded": True, "source_count": 2}


def test_blocked_result_remains_blocked():
    contract = ProviderExecutionResultContract()
    result = contract.normalize(
        {
            "status": "blocked",
            "execution_performed": False,
            "reason": "model_adapter_unavailable",
            "request": {"model_name": "missing-model"},
        },
        "missing-model",
    )

    assert result["status"] == "blocked"
    assert result["execution_performed"] is False
    assert result["reason"] == "model_adapter_unavailable"


def test_failure_envelope_does_not_expose_exception_details():
    contract = ProviderExecutionResultContract()
    result = contract.failure(
        "fake-model",
        request={"provider_name": "fake-provider", "model_name": "fake-model"},
    )

    assert result == {
        "status": "failed",
        "execution_performed": True,
        "reason": "provider_execution_failed",
        "model": "fake-model",
        "request": {
            "provider_name": "fake-provider",
            "model_name": "fake-model",
        },
    }
    assert "secret" not in str(result)


def test_invalid_execution_status_is_rejected():
    with pytest.raises(ValueError, match="status"):
        ProviderExecutionResultContract().normalize(
            {"status": "unknown"},
            "fake-model",
        )


def test_invalid_model_result_is_rejected():
    with pytest.raises(ValueError, match="model result"):
        ProviderExecutionResultContract().normalize(
            {
                "status": "completed",
                "result": {"provider": "fake-provider"},
            },
            "fake-model",
        )


def test_executor_normalizes_successful_adapter_result():
    adapter = FakeAdapter()
    executor = ProviderInvocationExecutor(adapter_resolver=lambda _: adapter)

    result = executor.execute("fake-provider", "fake-model", "hello")

    assert result["status"] == "completed"
    assert result["execution_performed"] is True
    assert result["result"]["text"] == "normalized response"
    assert adapter.calls == 1


def test_executor_converts_provider_exception_to_stable_failure():
    adapter = FakeAdapter(error=RuntimeError("secret provider failure details"))
    executor = ProviderInvocationExecutor(adapter_resolver=lambda _: adapter)

    result = executor.execute("fake-provider", "fake-model", "hello")

    assert result["status"] == "failed"
    assert result["execution_performed"] is True
    assert result["reason"] == "provider_execution_failed"
    assert "secret provider failure details" not in str(result)
    assert adapter.calls == 1


def test_executor_does_not_execute_when_adapter_is_unavailable():
    executor = ProviderInvocationExecutor(adapter_resolver=lambda _: None)

    result = executor.execute("fake-provider", "missing-model", "hello")

    assert result["status"] == "blocked"
    assert result["execution_performed"] is False
    assert result["reason"] == "model_adapter_unavailable"
