import unittest

from backend.app.reality.retrieval_engine import RealityRetrievalEngine
from backend.app.reality.retrieval_provider_executor import RetrievalProviderExecutor


class SuccessfulProvider:
    name = "test_provider"

    def retrieve(self, request):
        return {
            "status": "completed",
            "provider": self.name,
            "sources": [{"id": "source-1", "title": "Test source"}],
            "content": "Evidence content",
        }


class FailingProvider:
    name = "failing_provider"

    def retrieve(self, request):
        raise RuntimeError("private provider failure details")


class MalformedProvider:
    name = "malformed_provider"

    def retrieve(self, request):
        return {"status": "completed", "sources": "not-a-list", "content": "bad"}


class Step60RetrievalProviderExecutionBoundaryTests(unittest.TestCase):
    def test_executor_returns_stable_completed_contract(self):
        request = {"query": "current information", "source_type": "web"}
        result = RetrievalProviderExecutor().execute(SuccessfulProvider(), request)

        self.assertEqual(result["status"], "completed")
        self.assertTrue(result["retrieval_executed"])
        self.assertEqual(result["provider"], "test_provider")
        self.assertEqual(result["request"], request)
        self.assertEqual(result["sources"][0]["id"], "source-1")

    def test_executor_contains_provider_failure(self):
        request = {"query": "current information"}
        result = RetrievalProviderExecutor().execute(FailingProvider(), request)

        self.assertEqual(result["status"], "failed")
        self.assertTrue(result["retrieval_executed"])
        self.assertEqual(result["reason"], "retrieval_provider_failed")
        self.assertNotIn("private provider failure details", str(result))

    def test_executor_rejects_malformed_provider_output(self):
        request = {"query": "current information"}
        result = RetrievalProviderExecutor().execute(MalformedProvider(), request)

        self.assertEqual(result["status"], "failed")
        self.assertEqual(result["reason"], "retrieval_provider_failed")

    def test_engine_uses_injected_provider_executor(self):
        calls = []

        class RecordingExecutor:
            def execute(self, provider, request):
                calls.append((provider, request))
                return {
                    "status": "completed",
                    "provider": "injected_provider",
                    "request": dict(request),
                    "sources": [],
                    "content": "injected content",
                    "retrieval_executed": True,
                }

        request = {"query": "current information"}
        engine = RealityRetrievalEngine(
            provider=SuccessfulProvider(),
            provider_executor=RecordingExecutor(),
        )
        result = engine.retrieve({"status": "required", "request": request})

        self.assertEqual(result["provider"], "injected_provider")
        self.assertEqual(result["content"], "injected content")
        self.assertEqual(len(calls), 1)
        self.assertIsInstance(calls[0][0], SuccessfulProvider)
        self.assertEqual(calls[0][1], request)

    def test_not_required_retrieval_does_not_invoke_provider_executor(self):
        class UnexpectedExecutor:
            def execute(self, provider, request):
                raise AssertionError("provider executor must not run")

        engine = RealityRetrievalEngine(provider_executor=UnexpectedExecutor())
        result = engine.retrieve({"status": "not_required", "request": None})

        self.assertEqual(result["status"], "not_required")
        self.assertFalse(result["retrieval_executed"])


if __name__ == "__main__":
    unittest.main()
