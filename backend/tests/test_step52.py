import pytest

from backend.app.models.provider_execution_result import ProviderExecutionResultContract
from backend.app.models.provider_invocation_executor import ProviderInvocationExecutor


class FakeAdapter:
    def __init__(self, result=None, error=None):
        self.result = result or {"text": "fake response", "model": "fake-model", "provider": "fake-provider"}
        self.error = error
        self.calls = []

    def generate(self, task, context=None):
        self.calls.append((task, context))
        if self.error is not None:
            raise self.error
        return self.result


def test_completed_result_uses_model_response_contract():
    result = ProviderExecutionResultContract().completed(
        {"text": "hello", "model": "model-a", "provider": "provider-a"}, "model-a"
    )
    assert result == {"status": "completed", "execution_performed": True, "result": {"text": "hello", "model": "model-a", "provider": "provider-a"}}


def test_completed_result_rejects_malformed_model_output():
    with pytest.raises(ValueError, match="non-empty text"):
        ProviderExecutionResultContract().completed({"text": ""}, "model-a")


def test_failure_result_is_stable_without_exception_message():
    request = {"provider_name": "provider-a", "model_name": "model-a", "task": "hello", "context": None}
    result = ProviderExecutionResultContract().failed("provider-a", "model-a", request)
    assert result == {"status": "failed", "execution_performed": True, "provider": "provider-a", "model": "model-a", "reason": "provider_execution_failed", "request": request}


def test_blocked_result_preserves_non_execution_state():
    request = {"provider_name": "provider-a", "model_name": "model-a", "task": "hello", "context": None}
    result = ProviderExecutionResultContract().blocked("provider-a", "model-a", request)
    assert result["status"] == "blocked"
    assert result["execution_performed"] is False
    assert result["reason"] == "model_adapter_unavailable"


def test_executor_normalizes_successful_adapter_output():
    adapter = FakeAdapter()
    result = ProviderInvocationExecutor(adapter_resolver=lambda _: adapter).execute("fake-provider", "fake-model", "hello")
    assert result["status"] == "completed"
    assert result["execution_performed"] is True
    assert result["result"] == {"text": "fake response", "model": "fake-model", "provider": "fake-provider"}


def test_executor_passes_context_and_preserves_request():
    adapter = FakeAdapter()
    context = {"grounded": True, "source_count": 2}
    result = ProviderInvocationExecutor(adapter_resolver=lambda _: adapter).execute("fake-provider", "fake-model", "hello", context=context)
    assert adapter.calls == [("hello", context)]
    assert result["request"]["context"] == context


def test_executor_converts_provider_exception_to_stable_failure():
    adapter = FakeAdapter(error=RuntimeError("secret provider detail"))
    result = ProviderInvocationExecutor(adapter_resolver=lambda _: adapter).execute("fake-provider", "fake-model", "hello")
    assert result["status"] == "failed"
    assert result["execution_performed"] is True
    assert result["reason"] == "provider_execution_failed"
    assert "secret provider detail" not in str(result)


def test_executor_does_not_expose_exception_text():
    adapter = FakeAdapter(error=ValueError("api-key=super-secret"))
    result = ProviderInvocationExecutor(adapter_resolver=lambda _: adapter).execute("fake-provider", "fake-model", "hello")
    assert result["status"] == "failed"
    assert "super-secret" not in str(result)
    assert "api-key" not in str(result)


def test_executor_keeps_adapter_unavailable_as_blocked():
    result = ProviderInvocationExecutor(adapter_resolver=lambda _: None).execute("fake-provider", "missing-model", "hello")
    assert result["status"] == "blocked"
    assert result["execution_performed"] is False
    assert result["reason"] == "model_adapter_unavailable"


def test_executor_rejects_invalid_invocation_before_adapter_resolution():
    calls = []
    def resolver(model_name):
        calls.append(model_name)
        return FakeAdapter()
    executor = ProviderInvocationExecutor(adapter_resolver=resolver)
    with pytest.raises(ValueError, match="task"):
        executor.execute("fake-provider", "fake-model", " ")
    assert calls == []


def test_result_contract_validates_request_shape():
    with pytest.raises(ValueError, match="request"):
        ProviderExecutionResultContract().failed("provider-a", "model-a", None)
