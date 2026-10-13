"""Non-secret canonical request identity for single-source claim checks.

This SHA-256 binds reply to normalized client parameters; it is NOT a MAC,
signature, bearer token, publisher attestation, or transport authentication.
"""

import hashlib
import json

from backend.app.api.original_source_claim import OriginalSourceClaimRequest


def claim_request_binding_sha256(request: OriginalSourceClaimRequest) -> str:
    if not isinstance(request, OriginalSourceClaimRequest):
        raise TypeError("request must be a validated original-source claim request")
    canonical = json.dumps(
        request.model_dump(mode="json"), sort_keys=True,
        separators=(",", ":"), ensure_ascii=True, allow_nan=False,
    ).encode("utf-8")
    return hashlib.sha256(canonical).hexdigest()


__all__ = ["claim_request_binding_sha256"]
