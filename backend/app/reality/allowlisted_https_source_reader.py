"""Operator-configured HTTPS reader for independently observed original source bytes.

Unlike a URL-only claim, this reader makes a *real* HTTPS GET directly to
one of a small set of operator-allowlisted exact URLs. DNS is resolved once,
all returned addresses must be globally routable, and the connection is
pinned to a checked address before standard TLS certificate/hostname
validation. Redirects are rejected; no proxy or arbitrary URL fetching.

A successful read establishes observed page content, NOT factual truth,
publisher endorsement, or semantic entailment.
"""

from __future__ import annotations

from datetime import datetime, timezone
from hashlib import sha256
from html.parser import HTMLParser
import http.client
from ipaddress import ip_address
import math
import re
import socket
import ssl
import zlib
from typing import Any, Callable, Iterable
from urllib.parse import urlsplit

from backend.app.reality.independent_source_text_assurance import (
    MAX_INDEPENDENT_SOURCE_TEXT_CHARS,
    _safe_observer_source_uri,
)


MAX_ALLOWED_SOURCE_URLS = 20
MAX_ALLOWED_SOURCE_URL_CHARS = 2048
DEFAULT_RESPONSE_BYTES_LIMIT = 256_000
DEFAULT_TIMEOUT_SECONDS = 5.0


def _checked_global_addresses(hostname: str) -> list[tuple[Any, ...]]:
    """Reject *all* DNS replies when any local/non-global result is found."""
    records = socket.getaddrinfo(
        hostname, 443, type=socket.SOCK_STREAM, proto=socket.IPPROTO_TCP
    )
    if not records or len(records) > 16:
        raise ValueError("source DNS returned an unsupported address set")
    checked: list[tuple[Any, ...]] = []
    for record in records:
        family, socktype, protocol, _, sockaddr = record
        if (
            family not in (socket.AF_INET, socket.AF_INET6)
            or socktype != socket.SOCK_STREAM
            or not isinstance(sockaddr, tuple)
            or len(sockaddr) < 2
            or sockaddr[1] != 443
        ):
            raise ValueError("source DNS returned an unsupported address")
        try:
            address = ip_address(sockaddr[0])
        except ValueError as exc:
            raise ValueError("source DNS returned an invalid address") from exc
        if not address.is_global:
            raise ValueError("source DNS returned a non-global address")
        checked.append((family, socktype, protocol, sockaddr))
    return checked


class _PinnedHttpsConnection(http.client.HTTPSConnection):
    """Pin the TCP destination to prevalidated DNS while using hostname SNI."""

    def connect(self) -> None:
        addresses = _checked_global_addresses(self.host)
        family, socktype, protocol, sockaddr = addresses[0]
        raw = socket.socket(family, socktype, protocol)
        try:
            raw.settimeout(self.timeout)
            raw.connect(sockaddr)
            # create_default_context() verifies chain and hostname;
            # the original hostname is retained for SNI and verification.
            self.sock = self._context.wrap_socket(
                raw, server_hostname=self.host
            )
        except BaseException:
            raw.close()
            raise


class _VisibleHtmlText(HTMLParser):
    """Conservative structural text extraction, NOT browser visibility.

    Discard common hidden DOM descendants before exact-text comparison. This
    does not execute CSS, JavaScript or a full HTML layout engine; visibility
    claims must not be inferred from a successful excerpt match.
    """

    _HIDDEN = frozenset({
        "script", "style", "head", "noscript", "svg", "template",
        "iframe", "object", "canvas",
    })
    _VOID = frozenset({
        "area", "base", "br", "col", "embed", "hr", "img", "input",
        "link", "meta", "param", "source", "track", "wbr",
    })
    # Text from distinct structural units must never become one continuous
    # quote just because the extraction strips HTML tags. Conservative
    # boundaries may reject multi-paragraph submissions (fail closed).
    _BLOCK = frozenset({
        "address", "article", "aside", "blockquote", "caption", "dd",
        "details", "dialog", "div", "dl", "dt", "fieldset", "figcaption",
        "figure", "footer", "form", "h1", "h2", "h3", "h4", "h5",
        "h6", "header", "hgroup", "legend", "li", "main", "nav",
        "ol", "p", "pre", "section", "summary", "table", "tbody",
        "td", "tfoot", "th", "thead", "tr", "ul",
    })
    _BLOCK_BREAK_VOID = frozenset({"br", "hr"})
    _MAX_NESTING = 256

    def __init__(self) -> None:
        super().__init__(convert_charrefs=True)
        self._stack: list[tuple[str, bool]] = []
        self._suppressed = 0
        self.parts: list[str] = []

    @staticmethod
    def _has_hiding_attributes(
        tag: str, attrs: list[tuple[str, str | None]]
    ) -> bool:
        # Never collapse duplicated HTML attributes into a dict: some
        # browsers prioritize the FIRST occurrence, and a forged second
        # attribute could otherwise undo a hidden declaration here.
        if any(name in {"hidden", "inert"} for name, _ in attrs):
            return True
        if any(
            name == "aria-hidden" and (value or "").strip().casefold() == "true"
            for name, value in attrs
        ):
            return True
        # A closed <details> element's body is not reliably exposed to a
        # reader. Conservatively omit the entire element, including summary.
        if tag == "details" and not any(name == "open" for name, _ in attrs):
            return True
        for name, style in attrs:
            if name != "style" or style is None:
                continue
            # CSS comments may be placed between tokens; remove them before
            # checking simple inline declarations. We do not parse external
            # stylesheets, CSS variables or JavaScript-driven visibility.
            clean = re.sub(r"/\*.*?\*/", "", style, flags=re.DOTALL)
            for declaration in clean.split(";"):
                property_name, sep, value = declaration.partition(":")
                if not sep:
                    continue
                prop = property_name.strip().casefold()
                setting = re.sub(
                    r"\s*!\s*important\s*$", "", value, flags=re.IGNORECASE
                ).strip().casefold()
                if (
                    (prop == "display" and setting == "none")
                    or (prop == "visibility" and setting in {"hidden", "collapse"})
                    or (prop == "content-visibility" and setting == "hidden")
                ):
                    return True
        return False

    def handle_starttag(
        self, tag: str, attrs: list[tuple[str, str | None]]
    ) -> None:
        if tag in self._VOID:
            if tag in self._BLOCK_BREAK_VOID and self._suppressed == 0:
                self._boundary()
            return
        if len(self._stack) >= self._MAX_NESTING:
            raise ValueError("source HTML nesting exceeds safety bound")
        suppressed = tag in self._HIDDEN or self._has_hiding_attributes(
            tag, attrs
        )
        # Do not silently stitch visible words from opposite sides of an
        # excluded subtree into a seemingly publisher-observed statement.
        if (suppressed or tag in self._BLOCK) and self._suppressed == 0:
            self._boundary()
        self._stack.append((tag, suppressed))
        if suppressed:
            self._suppressed += 1

    def handle_endtag(self, tag: str) -> None:
        # Unwind to the matching opening tag. If markup is malformed and
        # closes a parent early, keep the whole discarded subtree excluded;
        # stray end tags cannot reveal hidden text.
        for index in range(len(self._stack) - 1, -1, -1):
            if self._stack[index][0] == tag:
                removed = self._stack[index:]
                self._stack = self._stack[:index]
                old_suppression = self._suppressed
                self._suppressed -= sum(flag for _, flag in removed)
                if self._suppressed == 0 and (
                    old_suppression > 0
                    or any(open_tag in self._BLOCK for open_tag, _ in removed)
                ):
                    self._boundary()
                return

    def _boundary(self) -> None:
        if self.parts and self.parts[-1] != "\n":
            self.parts.append("\n")

    def handle_data(self, data: str) -> None:
        if self._suppressed == 0:
            self.parts.append(data)

    def text(self) -> str:
        # Preserve excluded-subtree boundaries as newlines. Generic global
        # whitespace collapsing would manufacture quoted sentences by
        # joining text around hidden DOM regions.
        lines = " ".join(self.parts).split("\n")
        return "\n".join(
            normalized for line in lines
            if (normalized := " ".join(line.split()))
        )


def _decode_observed_content(raw: bytes, content_type: str) -> str:
    tokens = [value.strip().lower() for value in content_type.split(";")]
    mime = tokens[0]
    if mime not in {"text/html", "text/plain"}:
        raise ValueError("unsupported source media type")
    for token in tokens[1:]:
        if token.startswith("charset="):
            charset = token.partition("=")[2].strip("\"'")
            if charset not in {"utf-8", "utf8", "us-ascii"}:
                raise ValueError("unsupported source character encoding")
    decoded = raw.decode("utf-8", errors="strict")
    if mime == "text/html":
        parser = _VisibleHtmlText()
        parser.feed(decoded)
        content = parser.text()
    else:
        content = decoded
    if not content.strip() or len(content) > MAX_INDEPENDENT_SOURCE_TEXT_CHARS:
        raise ValueError("invalid or oversized observed source text")
    return content


def _bounded_gzip_decode(body: bytes, *, limit: int) -> bytes:
    """Decode a *single* gzip stream with a hard decoded-byte ceiling.

    Never accept gzip bombs, partial streams, trailing bytes, extra members or
    invalid checksums. SHA256 audit remains over original HTTP response bytes.
    """
    try:
        decoder = zlib.decompressobj(wbits=16 + zlib.MAX_WBITS)
        decoded = decoder.decompress(body, limit + 1)
        if len(decoded) > limit or decoder.unconsumed_tail:
            raise ValueError("decoded source response exceeds byte limit")
        decoded += decoder.flush(limit + 1 - len(decoded))
        if len(decoded) > limit:
            raise ValueError("decoded source response exceeds byte limit")
        if not decoder.eof or decoder.unused_data:
            raise ValueError("invalid or incomplete gzip source response")
        return decoded
    except zlib.error as exc:
        raise ValueError("invalid or incomplete gzip source response") from exc


class AllowlistedHttpsSourceReader:
    """A real HTTPS reader, off unless exact URLs are configured by operator."""

    def __init__(
        self,
        allowed_urls: Iterable[str],
        *,
        timeout_seconds: float = DEFAULT_TIMEOUT_SECONDS,
        max_response_bytes: int = DEFAULT_RESPONSE_BYTES_LIMIT,
        clock: Callable[[], datetime] | None = None,
        connection_factory: Callable[..., Any] | None = None,
    ) -> None:
        if isinstance(allowed_urls, (str, bytes)):
            raise ValueError("allowed_urls must be a collection of full URLs")
        try:
            urls = tuple(allowed_urls)
        except TypeError as exc:
            raise ValueError("allowed_urls must be iterable") from exc
        if (
            not urls or len(urls) > MAX_ALLOWED_SOURCE_URLS
            or len(set(urls)) != len(urls)
        ):
            raise ValueError("operator must allowlist 1–20 unique source URLs")
        for url in urls:
            if (
                not isinstance(url, str)
                or not 1 <= len(url) <= MAX_ALLOWED_SOURCE_URL_CHARS
                or not _safe_observer_source_uri(url)
            ):
                raise ValueError("invalid operator-allowlisted HTTPS source URL")
        if (
            not isinstance(timeout_seconds, (int, float))
            or isinstance(timeout_seconds, bool)
            or not math.isfinite(timeout_seconds)
            or not 0 < timeout_seconds <= 15
        ):
            raise ValueError("timeout_seconds must be finite and within (0, 15]")
        if (
            not isinstance(max_response_bytes, int)
            or isinstance(max_response_bytes, bool)
            or not 0 < max_response_bytes <= 1_000_000
        ):
            raise ValueError("max_response_bytes must be within 1–1000000")
        if clock is not None and not callable(clock):
            raise ValueError("clock must be callable")
        if connection_factory is not None and not callable(connection_factory):
            raise ValueError("connection_factory must be callable")

        self._allowed = frozenset(urls)
        self._timeout = float(timeout_seconds)
        self._max_bytes = max_response_bytes
        self._clock = clock or (lambda: datetime.now(timezone.utc))
        # Only backend-installed code can override the transport for tests.
        self._connection_factory = connection_factory or _PinnedHttpsConnection

    def __call__(self, uri: str) -> dict[str, Any]:
        if not isinstance(uri, str) or uri not in self._allowed:
            raise ValueError("source URL is not operator allowlisted")
        if not _safe_observer_source_uri(uri):
            raise ValueError("unsafe source URL")
        parsed = urlsplit(uri)
        host = parsed.hostname
        assert host is not None  # already validated
        path = parsed.path or "/"
        if parsed.query:
            path += "?" + parsed.query

        context = ssl.create_default_context()
        conn = self._connection_factory(
            host, 443, timeout=self._timeout, context=context
        )
        try:
            conn.request(
                "GET", path,
                headers={
                    "Accept": "text/html, text/plain",
                    "Accept-Encoding": "identity",
                    "User-Agent": "AI-Reality-Layer-SourceReader/0.1",
                    "Connection": "close",
                },
            )
            response = conn.getresponse()
            # Reject redirects (including same-host) instead of following a
            # second, unchecked destination.
            if response.status != 200:
                raise ValueError("source HTTP response was not 200")
            encoding = response.getheader("Content-Encoding", "identity").strip().lower()
            if encoding not in {"identity", "gzip"}:
                label = encoding if encoding in {"br", "deflate", "zstd"} else "other"
                raise ValueError("unsupported source content encoding: " + label)
            declared_length = response.getheader("Content-Length")
            if declared_length is not None:
                if not declared_length.isdecimal():
                    raise ValueError("invalid source content length")
                if int(declared_length) > self._max_bytes:
                    raise ValueError("source response exceeds byte limit")
            content_type = response.getheader("Content-Type", "")
            raw = response.read(self._max_bytes + 1)
            if len(raw) > self._max_bytes:
                raise ValueError("source response exceeds byte limit")
            if declared_length is not None and int(declared_length) != len(raw):
                raise ValueError("incomplete source response body")
        finally:
            conn.close()

        observed = self._clock()
        if not isinstance(observed, datetime) or observed.tzinfo is None:
            raise ValueError("reader clock must be timezone-aware")
        decoded_bytes = (
            _bounded_gzip_decode(raw, limit=self._max_bytes)
            if encoding == "gzip" else raw
        )
        rendered = _decode_observed_content(decoded_bytes, content_type)
        return {
            "uri": uri,
            "content": rendered,
            "capture_sha256": sha256(raw).hexdigest(),
            "capture_observed_at": observed.astimezone(timezone.utc)
            .isoformat().replace("+00:00", "Z"),
        }


__all__ = ["AllowlistedHttpsSourceReader"]
