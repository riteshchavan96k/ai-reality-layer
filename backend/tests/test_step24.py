import unittest
from types import SimpleNamespace

from fastapi.exceptions import RequestValidationError
from pydantic import ValidationError

from backend.app.api.errors import unhandled_exception_handler, validation_exception_handler
from backend.app.api.request_id import RequestIdMiddleware
from backend.app.main import SolveRequest, app


class TestStep24(unittest.TestCase):
    def test_task_validation_rejects_empty_task(self):
        with self.assertRaises(ValidationError):
            SolveRequest(task="")

    def test_task_validation_rejects_oversized_task(self):
        with self.assertRaises(ValidationError):
            SolveRequest(task="x" * 10_001)

    def test_task_validation_accepts_valid_task(self):
        request = SolveRequest(task="Tell me about AI")
        self.assertEqual(request.task, "Tell me about AI")
        self.assertFalse(request.human_approved)

    def test_api_has_health_and_solve_routes(self):
        routes = {route.path for route in app.routes}
        self.assertIn("/health", routes)
        self.assertIn("/api/v1/solve", routes)

    def test_request_id_middleware_is_registered(self):
        middleware_classes = {middleware.cls for middleware in app.user_middleware}
        self.assertIn(RequestIdMiddleware, middleware_classes)

    def test_validation_error_handler_returns_safe_error_contract(self):
        request = SimpleNamespace(state=SimpleNamespace(request_id="test-request"))
        exc = RequestValidationError(
            [
                {
                    "type": "string_too_short",
                    "loc": ("body", "task"),
                    "msg": "String should have at least 1 character",
                    "input": "",
                    "ctx": {"min_length": 1},
                }
            ]
        )

        response = validation_exception_handler(request, exc)
        self.assertEqual(response.status_code, 422)
        self.assertEqual(response.body[0], ord("{"))
        self.assertIn(b"validation_error", response.body)
        self.assertIn(b"test-request", response.body)

    def test_unhandled_error_handler_does_not_expose_exception_details(self):
        request = SimpleNamespace(state=SimpleNamespace(request_id="test-request"))
        response = unhandled_exception_handler(request, RuntimeError("secret detail"))

        self.assertEqual(response.status_code, 500)
        self.assertIn(b"internal_error", response.body)
        self.assertIn(b"test-request", response.body)
        self.assertNotIn(b"secret detail", response.body)


if __name__ == "__main__":
    unittest.main()
