import unittest

from backend.app.reality.http_retrieval_provider import HttpRetrievalProvider
from backend.app.reality.retrieval_provider_executor import RetrievalProviderExecutor
from backend.app.reality.retrieval_provider_request import RetrievalProviderRequest
from backend.app.reality.retrieval_provider_response import RetrievalProviderResponse


class ProviderNameOnly:
    provider_name = "provider_name_only"

    def retrieve(self, request):
        raise RuntimeError("simulated failure")


class NameOnly:
    name = "name_only"

    def retrieve(self, request):
        raise RuntimeError("simulated failure")


class InvalidIdentity:
    provider_name = 123
    name = ""

    def retrieve(self, request):
        raise RuntimeError("simulated failure")


class SuccessfulProvider:
    provider_name = "successful_provider"

    def retrieve(self, request):
        return RetrievalProviderResponse(
            status="completed",
            sources=({"uri": "https://example.test/source"},),
            content="retrieved",
        )


class Step143ProviderIdentityTests(unittest.TestCase):
    def setUp(self):
        self.request = RetrievalProviderRequest(
            query="current reality",
            source_type="live_web",
            temporal_scope="current",
        )

    def test_provider_name_identity_is_preserved(self):
        result = RetrievalProviderExecutor().execute(ProviderNameOnly(), self.request)
        self.assertEqual(result["status"], "failed")
        self.assertEqual(result["provider"], "provider_name_only")

    def test_legacy_name_identity_is_preserved(self):
        result = RetrievalProviderExecutor().execute(NameOnly(), self.request)
        self.assertEqual(result["status"], "failed")
        self.assertEqual(result["provider"], "name_only")

    def test_invalid_identity_fails_without_inventing_provider_name(self):
        result = RetrievalProviderExecutor().execute(InvalidIdentity(), self.request)
        self.assertEqual(result["status"], "failed")
        self.assertIsNone(result["provider"])

    def test_http_provider_identity_is_preserved_on_provider_failure(self):
        provider = HttpRetrievalProvider(
            "https://example.test/search?q={query}",
            opener=lambda request, timeout: (_ for _ in ()).throw(RuntimeError("network failure")),
        )
        result = RetrievalProviderExecutor().execute(provider, self.request)
        self.assertEqual(result["status"], "failed")
        self.assertEqual(result["provider"], "http_retrieval")

    def test_response_identity_still_takes_precedence_when_present(self):
        result = RetrievalProviderExecutor().execute(SuccessfulProvider(), self.request)
        self.assertEqual(result["status"], "completed")
        self.assertEqual(result["provider"], "successful_provider")


if __name__ == "__main__":
    unittest.main()
