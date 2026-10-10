"""Step 224: source HTML hidden-text confusion and conservative filtering tests.

Synthetic HTML fixture tests use no network. Step 222 maintains the separate
genuine publisher DNS/TLS live canary.
"""

from dataclasses import replace
from datetime import datetime, timedelta, timezone
from hashlib import sha256
import gzip

import pytest

from backend.app.api.reality_state import RealityStateResponse
from backend.app.orchestrator.dependencies import OrchestrationDependencies
from backend.app.orchestrator.orchestrator import build_reality_state_from_evidence
from backend.app.reality.allowlisted_https_source_reader import (
    AllowlistedHttpsSourceReader, _decode_observed_content,
)
from backend.app.reality.independent_source_text_assurance import (
    IndependentSourceTextAssurance,
)
from backend.app.reality.reality_state_builder import RealityStateBuilder
from backend.app.reality.source_freshness_evaluator import SourceFreshnessEvaluator


URI = "https://publisher.example.test/visible-evidence"
GENUINE = "Python 3.13.0 was released on October 7, 2024."
FORGED = "Python 3.13.0 was released on January 1, 1900."
CLOCK = datetime.now(timezone.utc) - timedelta(seconds=5)


def _markup(hidden: str, *, live: str = GENUINE) -> bytes:
    return ("<html><head><title>unrelated title</title></head><body>"
            + hidden + "<p>" + live + "</p></body></html>").encode()


HIDDEN_VARIANTS = (
    "<template>" + FORGED + "</template>",
    "<div hidden>" + FORGED + "</div>",
    "<div hidden='false'>" + FORGED + "</div>",
    "<p aria-hidden=' TRUE '>" + FORGED + "</p>",
    "<div inert>" + FORGED + "</div>",
    "<div style='display:none'>" + FORGED + "</div>",
    "<div style='display : /* comment */ none !important'>" + FORGED + "</div>",
    "<div style='display:none' style='color:green'>" + FORGED + "</div>",
    "<div aria-hidden='true' aria-hidden='false'>" + FORGED + "</div>",
    "<section style='VISIBILITY: HIDDEN'>" + FORGED + "</section>",
    "<div style='visibility: collapse'>" + FORGED + "</div>",
    "<article style='content-visibility:hidden'>" + FORGED + "</article>",
    "<details><summary>Expandable summary</summary>" + FORGED + "</details>",
    "<iframe>" + FORGED + "</iframe>",
    "<object>" + FORGED + "</object>",
    "<canvas>" + FORGED + "</canvas>",
)


@pytest.mark.parametrize("markup", HIDDEN_VARIANTS)
def test_hidden_claim_never_enters_rendered_source_text(markup):
    actual = _decode_observed_content(_markup(markup), "text/html; charset=utf-8")
    assert GENUINE in actual
    assert FORGED not in actual
    assert "unrelated title" not in actual


@pytest.mark.parametrize("markup", HIDDEN_VARIANTS)
def test_hidden_claim_alone_is_never_valid_visible_source_text(markup):
    with pytest.raises(ValueError, match="invalid or oversized observed"):
        _decode_observed_content(
            ("<body>" + markup + "</body>").encode(), "text/html"
        )


@pytest.mark.parametrize("markup", HIDDEN_VARIANTS)
def test_hidden_claim_fails_strict_https_reader_matching(markup):
    body = _markup(markup)
    class Response:
        status = 200
        def getheader(self, key, default=None):
            return {
                "Content-Type": "text/html; charset=utf-8",
                "Content-Length": str(len(body)),
            }.get(key, default)
        def read(self, limit):
            return body[:limit]
    class Connection:
        def __init__(self, *args, **kwargs):
            pass
        def request(self, *args, **kwargs):
            pass
        def getresponse(self):
            return Response()
        def close(self):
            pass

    reader = AllowlistedHttpsSourceReader(
        [URI], clock=lambda: CLOCK, connection_factory=Connection
    )
    assert reader(URI)["capture_sha256"] == sha256(body).hexdigest()
    deps = replace(
        OrchestrationDependencies.default(),
        independent_source_text_assurance=IndependentSourceTextAssurance(reader),
        reality_state_builder=RealityStateBuilder(clock=lambda: CLOCK),
        source_freshness_evaluator=SourceFreshnessEvaluator(clock=lambda: CLOCK),
    )
    def run(excerpt):
        output = build_reality_state_from_evidence(
            "When was Python 3.13.0 released?",
            [{"uri": URI, "content": excerpt}],
            entity="Python 3.13.0",
            freshness_max_age_seconds=3600,
            require_independent_source_text_match=True,
            dependencies=deps,
        )
        RealityStateResponse.model_validate(output)
        return output
    forged = run(FORGED)
    assert forged["status"] == "uncertain"
    assay = forged["evidence"]["independent_source_text_assurance"]
    assert assay["status"] == "unverified"
    assert assay["sources"][0]["reason"] == "submitted_text_not_in_observed_content"
    assert assay["publisher_authenticated"] is False
    assert assay["semantic_support_verified"] is False
    genuine = run(GENUINE)
    assert genuine["status"] == "supported"
    assert genuine["source_observation"]["observations"][0][
        "observation_method"
    ] == "independent_source_capture"


def test_regular_inline_tags_preserve_honest_contiguous_quote():
    html = "<p>Python 3.13.0 was released on <strong>October 7, 2024.</strong></p>"
    assert _decode_observed_content(html.encode(), "text/html") == GENUINE


def test_visible_content_in_open_details_remains_available():
    html = "<details open><summary>Release</summary><p>" + GENUINE + "</p></details>"
    extracted = _decode_observed_content(html.encode(), "text/html")
    assert "Release" in extracted and GENUINE in extracted


def test_void_and_self_closing_tags_do_not_trap_visible_text():
    html = "<head><meta charset=utf-8></head><body><br><img src=x><p>" + GENUINE + "</p></body>"
    assert _decode_observed_content(html.encode(), "text/html") == GENUINE


def test_malformed_hidden_subtree_does_not_release_hidden_claim():
    html = "<body><p hidden><span>" + FORGED + "</p><p>" + GENUINE + "</p></body>"
    extracted = _decode_observed_content(html.encode(), "text/html")
    assert FORGED not in extracted
    assert GENUINE in extracted


def test_extreme_nesting_fails_closed():
    payload = ("<div>" * 257 + GENUINE + "</div>" * 257).encode()
    with pytest.raises(ValueError, match="nesting exceeds safety bound"):
        _decode_observed_content(payload, "text/html")


def test_gzip_wrapped_hidden_markup_is_still_excluded():
    from backend.app.reality.allowlisted_https_source_reader import _bounded_gzip_decode
    original = _markup("<template>" + FORGED + "</template>")
    wire = gzip.compress(original)
    decoded = _bounded_gzip_decode(wire, limit=256_000)
    assert decoded == original
    rendered = _decode_observed_content(decoded, "text/html")
    assert FORGED not in rendered and GENUINE in rendered


def test_plain_text_is_not_mislabeled_as_browser_rendered_markup():
    plain = "<div hidden>" + FORGED + "</div>"
    assert _decode_observed_content(plain.encode(), "text/plain") == plain


def test_hidden_attribute_on_visible_parent_does_not_leak_nested_text():
    html = "<p hidden><strong>" + FORGED + "</strong></p><p>" + GENUINE + "</p>"
    assert _decode_observed_content(html.encode(), "text/html") == GENUINE
