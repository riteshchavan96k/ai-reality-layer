"""Opt-in *external* HTTPS smoke against an operator-owned restricted pilot.

Independent stdlib client (no application imports); never a substitute for an
approved deployment, independent reviewer or real-world factual evaluation.
No connections are attempted without --live, explicit host and env secret.
"""

from __future__ import annotations

import argparse
import http.client
from ipaddress import ip_address
import json
import os
import re
import socket
import ssl
from urllib.parse import urlsplit

SOURCE_URL = "https://www.python.org/downloads/release/python-3130/"
SOURCE_EXCERPT = "This is the stable release of Python 3.13.0"
CLAIM = "Python 3.13.0 is a stable release."
NEGATED_CLAIM = "Python 3.13.0 is not a stable release."
MAX_RESPONSE_BYTES = 384_000
MAX_BODY_BYTES = 4 * 1024 * 1024
TIMEOUT_SECONDS = 10
TOKEN_ENV = "ARL_STEP234_PROBE_BEARER_TOKEN"


class PilotProbeError(ValueError):
    """Fixed error without request, response, source or secret contents."""


def validate_endpoint(endpoint: str) -> str:
    """Require an external DNS hostname over standard HTTPS, with no URL extras."""
    if not isinstance(endpoint, str) or len(endpoint) > 255:
        raise PilotProbeError("invalid_endpoint")
    try:
        parsed = urlsplit(endpoint)
        host = parsed.hostname
        port = parsed.port
    except ValueError as exc:
        raise PilotProbeError("invalid_endpoint") from exc
    if (
        parsed.scheme != "https" or not host or port not in (None, 443)
        or parsed.username is not None or parsed.password is not None
        or parsed.path not in ("", "/") or parsed.query or parsed.fragment
        or not parsed.netloc or "@" in parsed.netloc
    ):
        raise PilotProbeError("invalid_endpoint")
    try:
        ip_address(host)
    except ValueError:
        pass
    else:
        raise PilotProbeError("endpoint_must_be_dns_hostname")
    try:
        ascii_host = host.encode("ascii").decode("ascii").lower()
    except UnicodeError as exc:
        raise PilotProbeError("invalid_endpoint_hostname") from exc
    labels = ascii_host.split(".")
    if (
        len(ascii_host) > 253 or len(labels) < 2
        or any(not re.fullmatch(r"[a-z0-9](?:[a-z0-9-]{0,61}[a-z0-9])?", x) for x in labels)
        or labels[-1] in {"local", "localhost", "internal", "test", "invalid", "example"}
    ):
        raise PilotProbeError("invalid_endpoint_hostname")
    return ascii_host


def _global_dns_records(host: str) -> list[tuple]:
    try:
        records = socket.getaddrinfo(host, 443, type=socket.SOCK_STREAM, proto=socket.IPPROTO_TCP)
    except OSError as exc:
        raise PilotProbeError("endpoint_dns_unavailable") from exc
    if not 1 <= len(records) <= 16:
        raise PilotProbeError("endpoint_dns_unacceptable")
    for family, kind, protocol, _canon, sockaddr in records:
        if (family not in (socket.AF_INET, socket.AF_INET6)
            or kind != socket.SOCK_STREAM or protocol != socket.IPPROTO_TCP
            or not isinstance(sockaddr, tuple) or len(sockaddr) < 2
            or sockaddr[1] != 443):
            raise PilotProbeError("endpoint_dns_unacceptable")
        try:
            valid = ip_address(sockaddr[0]).is_global
        except ValueError:
            valid = False
        if not valid:
            raise PilotProbeError("endpoint_dns_not_global")
    return records


class _PinnedTlsConnection(http.client.HTTPSConnection):
    def connect(self) -> None:
        family, kind, protocol, _canon, sockaddr = _global_dns_records(self.host)[0]
        raw = socket.socket(family, kind, protocol)
        try:
            raw.settimeout(self.timeout)
            raw.connect(sockaddr)
            self.sock = self._context.wrap_socket(raw, server_hostname=self.host)
        except BaseException:
            raw.close()
            raise


class ExternalPilotClient:
    """No proxies, redirects, source URL fetching or unaudited host changes."""

    def __init__(self, endpoint: str):
        self.host = validate_endpoint(endpoint)

    def send(self, method: str, path: str, *, token: str | None = None,
             body: dict | None = None, oversized: bool = False) -> tuple[int, dict]:
        if (method, path) not in {
            ("GET", "/health"), ("POST", "/api/v1/reality-state/evidence")
        }:
            raise PilotProbeError("probe_route_not_allowed")
        if oversized and (method != "POST" or body is not None):
            raise PilotProbeError("invalid_oversized_probe")
        encoded = json.dumps(body, separators=(",", ":")).encode("utf-8") if body is not None else b""
        if len(encoded) > MAX_BODY_BYTES:
            raise PilotProbeError("probe_body_too_large")
        conn = _PinnedTlsConnection(self.host, 443, timeout=TIMEOUT_SECONDS,
                                    context=ssl.create_default_context())
        try:
            conn.putrequest(method, path)
            conn.putheader("Accept", "application/json")
            conn.putheader("Accept-Encoding", "identity")
            conn.putheader("Connection", "close")
            if token is not None:
                conn.putheader("Authorization", "Bearer " + token)
            if method == "POST":
                conn.putheader("Content-Type", "application/json")
                conn.putheader("Content-Length", str(MAX_BODY_BYTES + 1 if oversized else len(encoded)))
            conn.endheaders()
            if encoded:
                conn.send(encoded)
            response = conn.getresponse()
            if 300 <= response.status <= 399:
                raise PilotProbeError("remote_redirect_refused")
            declared = response.getheader("Content-Length")
            if declared is not None and (not declared.isdecimal() or int(declared) > MAX_RESPONSE_BYTES):
                raise PilotProbeError("remote_response_too_large")
            raw = response.read(MAX_RESPONSE_BYTES + 1)
            if len(raw) > MAX_RESPONSE_BYTES:
                raise PilotProbeError("remote_response_too_large")
            try:
                parsed = json.loads(raw)
            except (UnicodeDecodeError, json.JSONDecodeError) as exc:
                raise PilotProbeError("remote_response_not_json") from exc
            if not isinstance(parsed, dict):
                raise PilotProbeError("remote_response_not_object")
            return response.status, parsed
        finally:
            conn.close()


def _require(ok: bool, reason: str) -> None:
    if not ok:
        raise PilotProbeError(reason)


def _payload(claim: str) -> dict:
    return {
        "task": "Check official Python release evidence in restricted pilot",
        "entity": "Python 3.13.0",
        "documents": [{"uri": SOURCE_URL, "content": SOURCE_EXCERPT}],
        "freshness_max_age_seconds": 3600,
        "require_independent_source_text_match": True,
        "require_claim_alignment": True,
        "claim_text": claim,
    }


def run_probe(send, token: str) -> dict:
    """Check exact public API behavior; never print response documents."""
    _require(isinstance(token, str) and 32 <= len(token.encode("utf-8")) <= 256
             and token.isascii() and not any(c.isspace() for c in token),
             "probe_secret_invalid")
    route = "/api/v1/reality-state/evidence"
    code, response = send("GET", "/health")
    _require(code == 200 and response.get("status") == "healthy"
             and response.get("service") == "ai-reality-layer", "health_failed")
    for bad in (None, token + "-incorrect"):
        code, response = send("POST", route, token=bad, body=_payload(CLAIM))
        _require(code == 401 and response == {"detail": "Unauthorized"}, "authorization_failed")
    code, response = send("POST", route, token=token, oversized=True)
    _require(code == 413 and response == {"detail": "Request body too large"}, "oversize_failed")
    code, response = send("POST", route, token=token, body=_payload(CLAIM))
    alignment = response.get("evidence", {}).get("claim_alignment", {})
    assurance = response.get("evidence", {}).get("independent_source_text_assurance", {})
    sources = assurance.get("sources", [])
    _require(code == 200 and response.get("status") == "supported"
             and alignment.get("status") == "aligned"
             and alignment.get("semantic_support_verified") is False
             and alignment.get("factual_truth_verified") is False
             and alignment.get("decision_reasons") == [
                 {"source_ref": SOURCE_URL, "code": "bounded_assertion_aligned"}]
             and len(sources) == 1 and sources[0].get("source_ref") == SOURCE_URL
             and re.fullmatch(r"[0-9a-f]{64}", sources[0].get("capture_sha256", "")) is not None
             and sources[0].get("capture_observed_at", "").endswith("Z"),
             "live_positive_evidence_failed")
    code, response = send("POST", route, token=token, body=_payload(NEGATED_CLAIM))
    alignment = response.get("evidence", {}).get("claim_alignment", {})
    _require(code == 200 and response.get("status") == "uncertain"
             and alignment.get("status") == "contradicted"
             and alignment.get("decision_reasons") == [
                 {"source_ref": SOURCE_URL, "code": "bounded_assertion_contradicted"}],
             "live_contradiction_refusal_failed")
    bad_source = _payload(CLAIM)
    bad_source["documents"][0]["uri"] = "https://www.python.org/not-an-allowlisted-step234-path"
    code, response = send("POST", route, token=token, body=bad_source)
    _require(code == 200 and response.get("status") != "supported", "nonallowlisted_source_supported")
    return {
        "audit": "step234_externally_executed_https_pilot_probe",
        "checks_passed": 7,
        "verified_behavior": ["health", "missing_token_401", "incorrect_token_401", "oversized_413",
                              "independent_original_source_positive", "bounded_claim_negation_refused",
                              "off_allowlist_not_supported"],
        "independent_human_labeled_accuracy": False,
        "complete_release_gate": False,
        "note": "Run from a machine outside the operator's hosting infrastructure; manual operations gates remain.",
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--endpoint", required=True, help="Operator-approved HTTPS origin (no path)")
    parser.add_argument("--live", action="store_true", help="Explicitly authorize live remote checks")
    args = parser.parse_args(argv)
    if not args.live:
        parser.error("network disabled by default; --live is required")
    try:
        client = ExternalPilotClient(args.endpoint)
        result = run_probe(client.send, os.environ.get(TOKEN_ENV, ""))
        print(json.dumps(result, sort_keys=True, separators=(",", ":")))
        return 0
    except Exception:
        # No exception, request, host, content, response, URL, token, or traceback.
        print("Step 234 external HTTPS probe failed (no sensitive details emitted)")
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
