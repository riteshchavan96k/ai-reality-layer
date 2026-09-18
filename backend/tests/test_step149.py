import unittest

from backend.app.reality.retrieval_engine import RealityRetrievalEngine, _blocked_selection_result
from backend.app.reality.retrieval_result import RetrievalResultContract


class _NonExecutableSelection:
    selection_executed = False
    reason = "selection_rejected"


class _NonExecutableSelector:
    def select(self, request):
        return _NonExecutableSelection()


class Step149BlockedRetrievalResultTests(unittest.TestCase):
    def setUp(self):
        self.request = {
            "query": "historical fact",
            "source_type": "live_web",
            "temporal_scope": "current",
            "required": True,
        }

    def test_blocked_selection_result_uses_canonical_contract(self):
        result = _blocked_selection_result(self.request, "selection_rejected")
        expected = RetrievalResultContract.blocked(
            self.request, provider=None, reason="selection_rejected"
        )
        self.assertEqual(result, expected)

    def test_blocked_result_has_canonical_execution_semantics(self):
        result = _blocked_selection_result(self.request, None)
        self.assertEqual(result["status"], "blocked")
        self.assertIsNone(result["provider"])
        self.assertEqual(result["sources"], [])
        self.assertIsNone(result["content"])
        self.assertFalse(result["retrieval_executed"])
        self.assertEqual(result["reason"], "retrieval_provider_unavailable")

    def test_engine_uses_canonical_contract_when_selection_is_not_executed(self):
        engine = RealityRetrievalEngine(provider_selector=_NonExecutableSelector())
        result = engine.retrieve({"status": "required", "request": self.request})
        expected = RetrievalResultContract.blocked(
            self.request, provider=None, reason="selection_rejected"
        )
        self.assertEqual(result, expected)


if __name__ == "__main__":
    unittest.main()
