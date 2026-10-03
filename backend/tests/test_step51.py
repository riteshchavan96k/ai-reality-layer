from backend.app.models.provider_invocation_executor import ProviderInvocationExecutor


class FakeAdapter:
    def __init__(self):
        self.calls = []

    def generate(self, task, context=None):
        self.calls.append((task, context))
        return {
            "text": "fake response",
            "model": "fake-model",
            "provider": "fake-provider",
        }


def test_executor_runs_adapter_with_invocation_contract():
    adapter = FakeAdapter()
    executor = ProviderInvocationExecutor(adapter_resolver=lambda _: adapter)

    result = executor.execute("fake-provider", "fake-model", "hello")

    assert result["status"] == "completed"
    assert result["execution_performed"] is True
    assert result["request"]["provider_name"] == "fake-provider"
    assert result["request"]["model_name"] == "fake-model"
    assert adapter.calls == [("hello", None)]


def test_executor_passes_context_to_adapter():
    adapter = FakeAdapter()
    context = {"grounded": True, "source_count": 2}
    executor = ProviderInvocationExecutor(adapter_resolver=lambda _: adapter)

    result = executor.execute("fake-provider", "fake-model", "hello", context=context)

    assert result["status"] == "completed"
    assert result["request"]["context"] == context
    assert adapter.calls == [("hello", context)]


def test_executor_blocks_when_adapter_is_unavailable():
    executor = ProviderInvocationExecutor(adapter_resolver=lambda _: None)

    result = executor.execute("fake-provider", "fake-model", "hello")

    assert result == {
        "status": "blocked",
        "execution_performed": False,
        "provider": "fake-provider",
        "model": "fake-model",
        "reason": "model_adapter_unavailable",
        "request": {
            "provider_name": "fake-provider",
            "model_name": "fake-model",
            "task": "hello",
            "context": None,
        },
    }


def test_executor_does_not_execute_when_adapter_is_unavailable():
    calls = []

    def resolver(model_name):
        calls.append(model_name)
        return None

    executor = ProviderInvocationExecutor(adapter_resolver=resolver)
    result = executor.execute("fake-provider", "fake-model", "hello")

    assert result["execution_performed"] is False
    assert calls == ["fake-model"]


def test_executor_rejects_invalid_provider_name():
    executor = ProviderInvocationExecutor(adapter_resolver=lambda _: FakeAdapter())

    try:
        executor.execute(" ", "fake-model", "hello")
    except ValueError as exc:
        assert "provider_name" in str(exc)
    else:
        raise AssertionError("expected provider_name validation error")


def test_executor_rejects_invalid_model_name():
    executor = ProviderInvocationExecutor(adapter_resolver=lambda _: FakeAdapter())

    try:
        executor.execute("fake-provider", " ", "hello")
    except ValueError as exc:
        assert "model_name" in str(exc)
    else:
        raise AssertionError("expected model_name validation error")


def test_executor_rejects_invalid_task():
    executor = ProviderInvocationExecutor(adapter_resolver=lambda _: FakeAdapter())

    try:
        executor.execute("fake-provider", "fake-model", " ")
    except ValueError as exc:
        assert "task" in str(exc)
    else:
        raise AssertionError("expected task validation error")


def test_executor_uses_real_internal_adapter_boundary():
    result = ProviderInvocationExecutor().execute(
        "internal", "mock-model", "hello"
    )

    assert result["status"] == "completed"
    assert result["execution_performed"] is True
    assert result["result"]["model"] == "mock-model"
    assert result["result"]["provider"] == "internal"
