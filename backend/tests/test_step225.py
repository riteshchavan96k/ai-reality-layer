"""Step 225: source quote contiguity across HTML structural boundaries.

Synthetic HTML tests deliberately do not prove factual truth, visual layout,
or publisher authenticity. Network is injected; live HTTPS CI remains separate.
"""

from dataclasses import replace
from datetime import datetime, timezone, timedelta
from hashlib import sha256

import pytest

from backend.app.api.reality_state import RealityStateResponse
from backend.app.orchestrator.dependencies import OrchestrationDependencies
from backend.app.orchestrator.orchestrator import build_reality_state_from_evidence
from backend.app.reality.allowlisted_https_source_reader import (
    _decode_observed_content, AllowlistedHttpsSourceReader,
)
from backend.app.reality.independent_source_text_assurance import (
    IndependentSourceTextAssurance,
)
from backend.app.reality.reality_state_builder import RealityStateBuilder
from backend.app.reality.source_freshness_evaluator import SourceFreshnessEvaluator


URI = "https://publisher.example.test/step225"
GENUINE = "Python 3.13.0 was released on October 7, 2024."
FORGED = "Python 3.13.0 was released on January 1, 1900."
PREFIX = "Python 3.13.0 was released on"
SUFFIX = "January 1, 1900."
TIME = datetime.now(timezone.utc) - timedelta(seconds=8)


CROSS_BLOCK = (
    "<p>" + PREFIX + "</p><p>" + SUFFIX + "</p>",
    "<div>" + PREFIX + "</div><div>" + SUFFIX + "</div>",
    "<article>" + PREFIX + "</article><article>" + SUFFIX + "</article>",
    "<h2>" + PREFIX + "</h2><p>" + SUFFIX + "</p>",
    "<ul><li>" + PREFIX + "</li><li>" + SUFFIX + "</li></ul>",
    "<dl><dt>" + PREFIX + "</dt><dd>" + SUFFIX + "</dd></dl>",
    "<table><tr><td>" + PREFIX + "</td><td>" + SUFFIX + "</td></tr></table>",
    "<table><tr><td>" + PREFIX + "</td></tr><tr><td>" + SUFFIX + "</td></tr></table>",
    "<p>" + PREFIX + "<br>" + SUFFIX + "</p>",
    "<p>" + PREFIX + "<hr>" + SUFFIX + "</p>",
    "<p>" + PREFIX + "</p>" + SUFFIX,
    "<section><p>" + PREFIX + "</p><p>" + SUFFIX + "</p></section>",
    "<blockquote>" + PREFIX + "</blockquote><p>" + SUFFIX + "</p>",
    "<div>" + PREFIX + "<p>" + SUFFIX + "</p></div>",
    "<header>" + PREFIX + "</header><main>" + SUFFIX + "</main>",
)

PRESERVED_INLINE = (
    "<p>Python 3.13.0 was released on <strong>October 7, 2024.</strong></p>",
    "<p>Python 3.13.0 was released on <span>October 7, 2024.</span></p>",
    "<div><p>Python 3.13.0 was released on <em>October 7, 2024.</em></p></div>",
    "<p>Python 3.13.0 was released on October 7, 2024.</p>",
)


def extracted(markup: str) -> str:
    return _decode_observed_content(
        ("<html><body>" + markup + "</body></html>").encode(),
        "text/html; charset=utf-8",
    )


@pytest.mark.parametrize("markup", CROSS_BLOCK)
def test_cross_block_forged_sentence_is_not_exact_source_text(markup):
    observed = extracted(markup)
    assert FORGED not in observed
    assert PREFIX in observed and SUFFIX in observed
    assert "\n" in observed


@pytest.mark.parametrize("markup", PRESERVED_INLINE)
def test_inline_quote_still_survives_as_one_substring(markup):
    assert GENUINE in extracted(markup)


@pytest.mark.parametrize("markup", (
    "<p>" + PREFIX + "<span hidden>not</span>" + SUFFIX + "</p>",
    "<p>" + PREFIX + "<template>not</template>" + SUFFIX + "</p>",
))
def test_hidden_subtree_boundaries_from_step224_are_preserved(markup):
    assert FORGED not in extracted(markup)


def test_plain_text_keeps_existing_semantics():
    assert _decode_observed_content(
        (PREFIX + " " + SUFFIX).encode(), "text/plain"
    ) == FORGED


def test_line_break_in_visible_quote_is_not_silently_joined():
    html = "<p>" + PREFIX + "<br>" + SUFFIX + "</p>"
    assert FORGED not in extracted(html)
    assert extracted(html).count("\n") >= 1


def test_consecutive_block_tags_do_not_create_blank_claim_segments():
    html = "<div><p>" + GENUINE + "</p></div><div><p>Another fact.</p></div>"
    assert extracted(html) == GENUINE + "\nAnother fact."


def test_strict_api_refuses_cross_paragraph_forgery_preserves_inline_truth():
    html = (
        "<html><body><p>" + PREFIX + "</p><p>" + SUFFIX + "</p>"
        + "<p>" + GENUINE.replace("October", "<strong>October</strong>")
        + "</p></body></html>"
    )
    wire = html.encode()
    class Response:
        status = 200
        def getheader(self, key, default=None):
            return {
                "Content-Type": "text/html; charset=utf-8",
                "Content-Length": str(len(wire)),
            }.get(key, default)
        def read(self, count):
            return wire[:count]
    class Transport:
        def __init__(self, *args, **kwargs):
            pass
        def request(self, *args, **kwargs):
            pass
        def getresponse(self):
            return Response()
        def close(self):
            pass
    reader = AllowlistedHttpsSourceReader(
        [URI], clock=lambda: TIME, connection_factory=Transport
    )
    assert reader(URI)["capture_sha256"] == sha256(wire).hexdigest()
    deps = replace(
        OrchestrationDependencies.default(),
        independent_source_text_assurance=IndependentSourceTextAssurance(reader),
        source_freshness_evaluator=SourceFreshnessEvaluator(clock=lambda: TIME),
        reality_state_builder=RealityStateBuilder(clock=lambda: TIME),
    )
    def state(quote: str):
        result = build_reality_state_from_evidence(
            "When was Python 3.13.0 released?",
            [{"uri": URI, "content": quote}],
            entity="Python 3.13.0",
            require_independent_source_text_match=True,
            freshness_max_age_seconds=3600,
            dependencies=deps,
        )
        RealityStateResponse.model_validate(result)
        return result

    forged = state(FORGED)
    assert forged["status"] == "uncertain"
    assert forged["evidence"]["independent_source_text_assurance"]["status"] == "unverified"
    assert forged["evidence"]["independent_source_text_assurance"]["sources"][0][
        "reason"
    ] == "submitted_text_not_in_observed_content"
    assert forged["evidence"]["independent_source_text_assurance"]["publisher_authenticated"] is False

    genuine = state(GENUINE)
    assert genuine["status"] == "supported"
    assert genuine["evidence"]["independent_source_text_assurance"]["status"] == "exact_text_observed"
    assert genuine["source_observation"]["observations"][0][
        "observation_method"
    ] == "independent_source_capture"
