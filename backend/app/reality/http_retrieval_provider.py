from __future__ import annotations

import json
from typing import Any, Callable
from urllib.parse import quote, urlparse
from urllib.request import Request, urlopen

from backend.app.reality.retrieval_provider_request import RetrievalProviderRequest
from backend.app.reality.retrieval_provider_response import RetrievalProviderResponse


class HttpRetrievalProvider:
    """Opt-in HTTPS adapter for a JSON retrieval endpoint."""

    provider_name = "http_retrieval"

    def __init__(self, endpoint_template: str, timeout_seconds: float = 10.0, max_response_bytes: int = 1_000_000, opener: Callable[..., Any] | None = None) -> None:
        if not isinstance(endpoint_template, str) or not endpoint_template.strip():
            raise ValueError("endpoint_template must be a non-empty string")
        if "{query}" not in endpoint_template:
            raise ValueError("endpoint_template must contain {query}")
        if not endpoint_template.startswith("https://"):
            raise ValueError("endpoint_template must use HTTPS")
        if not isinstance(timeout_seconds, (int, float)) or isinstance(timeout_seconds, bool) or timeout_seconds <= 0:
            raise ValueError("timeout_seconds must be a positive number")
        if not isinstance(max_response_bytes, int) or isinstance(max_response_bytes, bool) or max_response_bytes <= 0:
            raise ValueError("max_response_bytes must be a positive integer")
        self.endpoint_template = endpoint_template
        self.timeout_seconds = float(timeout_seconds)
        self.max_response_bytes = max_response_bytes
        self._opener = opener or urlopen

    def retrieve(self, request: RetrievalProviderRequest) -> RetrievalProviderResponse:
        if not isinstance(request, RetrievalProviderRequest):
            raise ValueError("request must be a RetrievalProviderRequest")
        url = self.endpoint_template.replace("{query}", quote(request.query, safe=""), 1)
        http_request = Request(url, headers={"Accept": "application/json", "User-Agent": "AI-Reality-Layer/0.1"}, method="GET")
        try:
            with self._opener(http_request, timeout=self.timeout_seconds) as response:
                payload = response.read(self.max_response_bytes + 1)
            if len(payload) > self.max_response_bytes:
                return RetrievalProviderResponse(status="failed", provider=self.provider_name, reason="response_too_large")
            decoded = json.loads(payload.decode("utf-8"))
            if not isinstance(decoded, dict):
                return RetrievalProviderResponse(status="failed", provider=self.provider_name, reason="invalid_json_object")
            return self._normalize_payload(decoded, url)
        except Exception:
            return RetrievalProviderResponse(status="failed", provider=self.provider_name, reason="http_retrieval_failed")

    def _normalize_payload(self, payload: dict[str, Any], request_url: str) -> RetrievalProviderResponse:
        status = payload.get("status", "completed")
        if status not in {"completed", "failed", "blocked", "provider_unavailable"}:
            return RetrievalProviderResponse(status="failed", provider=self.provider_name, reason="invalid_provider_status")
        reason = payload.get("reason")
        if reason is not None and (not isinstance(reason, str) or not reason.strip()):
            return RetrievalProviderResponse(status="failed", provider=self.provider_name, reason="invalid_provider_reason")
        content = payload.get("content")
        sources = payload.get("sources", [])
        if content is not None and not isinstance(content, str):
            return RetrievalProviderResponse(status="failed", provider=self.provider_name, reason="invalid_content")
        if not isinstance(sources, list) or any(not isinstance(source, dict) for source in sources):
            return RetrievalProviderResponse(status="failed", provider=self.provider_name, reason="invalid_sources")
        normalized_sources_list: list[dict[str, Any]] = []
        for source in sources:
            uri = source.get("uri")
            title = source.get("title")
            if uri is not None:
                if not isinstance(uri, str) or not uri.strip():
                    return RetrievalProviderResponse(status="failed", provider=self.provider_name, reason="invalid_source_uri")
                parsed = urlparse(uri)
                if parsed.scheme not in {"http", "https"} or not parsed.netloc:
                    return RetrievalProviderResponse(status="failed", provider=self.provider_name, reason="invalid_source_uri")
            if title is not None and not isinstance(title, str):
                return RetrievalProviderResponse(status="failed", provider=self.provider_name, reason="invalid_source_title")
            if uri is None and title is None:
                return RetrievalProviderResponse(status="failed", provider=self.provider_name, reason="source_missing_provenance")
            normalized_sources_list.append(dict(source))

        if status != "completed":
            if normalized_sources_list or content is not None:
                return RetrievalProviderResponse(
                    status="failed",
                    provider=self.provider_name,
                    reason="invalid_non_completed_payload",
                )
            return RetrievalProviderResponse(
                status=status,
                provider=self.provider_name,
                reason=reason,
            )

        # A retrieval endpoint is not the original publisher. Never fabricate a
        # source by substituting request_url when no source URI was returned.
        # Legacy source-less results can still be represented, but are not
        # accepted downstream as provenance-backed evidence.
        if any(source.get("uri") is None for source in normalized_sources_list):
            return RetrievalProviderResponse(
                status="failed", provider=self.provider_name,
                reason="source_uri_required",
            )
        uris = [source["uri"] for source in normalized_sources_list]
        if len(set(uris)) != len(uris):
            return RetrievalProviderResponse(
                status="failed", provider=self.provider_name,
                reason="duplicate_source_uri",
            )

        scoped = ["content" in source for source in normalized_sources_list]
        if any(scoped):
            if not all(scoped):
                return RetrievalProviderResponse(
                    status="failed", provider=self.provider_name,
                    reason="incomplete_source_scoped_content",
                )
            if any(
                not isinstance(source["content"], str)
                or not source["content"].strip()
                for source in normalized_sources_list
            ):
                return RetrievalProviderResponse(
                    status="failed", provider=self.provider_name,
                    reason="invalid_source_scoped_content",
                )
            joined = "\n\n".join(
                source["content"].strip() for source in normalized_sources_list
            )
            if content is not None and content.strip() != joined:
                return RetrievalProviderResponse(
                    status="failed", provider=self.provider_name,
                    reason="inconsistent_source_scoped_content",
                )
            content = joined

        return RetrievalProviderResponse(
            status="completed",
            sources=tuple(normalized_sources_list),
            content=content,
            provider=self.provider_name,
            reason=reason,
        )


__all__ = ["HttpRetrievalProvider"]
