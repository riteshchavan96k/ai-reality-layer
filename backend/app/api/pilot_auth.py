"""Fail-closed single-tenant access gate for an operator-controlled pilot.

Development behavior stays compatible with historical tests. A network-
reachable pilot MUST explicitly select pilot mode and configure a high-entropy
bearer token plus the existing independently observed HTTPS URL allowlist.
Ingress TLS, rate limiting, secret rotation and abuse controls belong to the
operator's deployment; this gate alone is not a production security claim.
"""

import hmac
from hashlib import sha256
import json
import os
from collections.abc import Mapping

from fastapi import Request
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware

from backend.app.reality.allowlisted_https_source_reader import AllowlistedHttpsSourceReader

_MIN_SECRET_BYTES = 32
_MAX_SECRET_BYTES = 256
_MAX_AUTHORIZATION_BYTES = 512


def pilot_runtime_configuration(
    environment: Mapping[str, str] | None = None,
) -> tuple[bool, bytes | None]:
    """Validate server-owned settings. Never return configured secrets to clients.

    The presence of a token in development mode is an error rather than
    silently disabling access control on a mistakenly deployed instance.
    """
    env = os.environ if environment is None else environment
    mode = env.get("ARL_RUNTIME_MODE", "development")
    token = env.get("ARL_PILOT_BEARER_TOKEN")
    if mode == "development":
        if token is not None:
            raise ValueError("pilot token requires ARL_RUNTIME_MODE=pilot")
        return False, None
    if mode != "pilot":
        raise ValueError("ARL_RUNTIME_MODE must be development or pilot")

    if not isinstance(token, str):
        raise ValueError("pilot bearer token is required")
    try:
        secret = token.encode("ascii")
    except UnicodeEncodeError as exc:
        raise ValueError("pilot bearer token must be printable ASCII") from exc
    if (
        len(secret) < _MIN_SECRET_BYTES
        or len(secret) > _MAX_SECRET_BYTES
        or any(byte < 33 or byte > 126 for byte in secret)
    ):
        raise ValueError("pilot bearer token must be 32-256 printable non-space ASCII bytes")

    raw_urls = env.get("ARL_INDEPENDENT_SOURCE_ALLOWED_URLS", "")
    try:
        allowed_urls = json.loads(raw_urls)
        # Validate exact URLs with the already shipping SSRF-conscious reader.
        # No DNS query or network request happens during configuration.
        AllowlistedHttpsSourceReader(allowed_urls)
    except (ValueError, TypeError, json.JSONDecodeError) as exc:
        raise ValueError("pilot requires a valid original-source HTTPS allowlist") from exc
    return True, secret


def _authorized(scope: dict, expected: bytes) -> bool:
    authorization = [
        value for name, value in scope.get("headers", [])
        if name.lower() == b"authorization"
    ]
    if len(authorization) != 1:
        return False
    value = authorization[0]
    if (
        len(value) > _MAX_AUTHORIZATION_BYTES
        or len(value) < 8
        or value[:7].lower() != b"bearer "
    ):
        return False
    candidate = value[7:]
    # Fixed-length digests prevent compare_digest leaking token length.
    return hmac.compare_digest(sha256(candidate).digest(), sha256(expected).digest())


class PilotAccessMiddleware(BaseHTTPMiddleware):
    """Guard *all* application paths except minimal process liveness."""

    async def dispatch(self, request: Request, call_next):
        try:
            enabled, token = pilot_runtime_configuration()
        except ValueError:
            # No fallback to unauthenticated development when pilot is broken.
            return JSONResponse(
                {"detail": "Service unavailable"},
                status_code=503,
                headers={"Cache-Control": "no-store"},
            )

        if not enabled or request.url.path == "/health":
            return await call_next(request)

        if token is None or not _authorized(request.scope, token):
            return JSONResponse(
                {"detail": "Unauthorized"},
                status_code=401,
                headers={
                    "WWW-Authenticate": "Bearer",
                    "Cache-Control": "no-store",
                },
            )
        response = await call_next(request)
        response.headers["Cache-Control"] = "no-store"
        response.headers["X-Content-Type-Options"] = "nosniff"
        return response


def main() -> int:
    """Container preflight: reject missing/invalid pilot settings at startup."""
    try:
        enabled, _ = pilot_runtime_configuration()
        if not enabled:
            raise ValueError("container must not start in development mode")
    except ValueError:
        print("Pilot configuration invalid; refusing to start.")
        return 1
    print("Pilot access configuration valid.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
