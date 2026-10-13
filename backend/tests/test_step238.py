"""Step238 security/functional contract: one original-source capture to shadow NLI.

Reader is monkeypatched IN TESTS ONLY; genuine reviewed original-source HTTPS
and pinned ONNX weights are separately exercised in Step238 GitHub CI.
"""

from copy import deepcopy
from datetime import datetime, timedelta, timezone
from hashlib import sha256
import json

import pytest

from backend.app.evaluation import step238_live_source_nli as s
from backend.app.reality.allowlisted_https_source_reader import AllowlistedHttpsSourceReader


CAPTURED = datetime(2026, 10, 13, 14, 0, 0, tzinfo=timezone.utc)
AT = CAPTURED + timedelta(seconds=20)
BODY = "Release details\n" + s.STANDALONE_ANCHOR + "\nOther unrelated official text"
HASH = sha256(BODY.encode("utf-8")).hexdigest()
UNIT_SHA = sha256(s.STANDALONE_ANCHOR.encode("utf-8")).hexdigest()


def observed(**kwargs):
    value = {
        "uri": s.SOURCE,
        "content": BODY,
        "capture_sha256": HASH,
        "capture_observed_at": CAPTURED.isoformat().replace("+00:00", "Z"),
        "observed_quote_unit_sha256": [],
    }
    value.update(kwargs)
    return value


class FakeModel:
    def __init__(self, *, invalid=None):
        self.calls = []
        self.invalid = invalid

    def predict(self, premise, hypothesis):
        self.calls.append((premise, hypothesis))
        if self.invalid is not None:
            return self.invalid
        relation = (
            "contradiction" if "not a stable" in hypothesis
            else "neutral" if "production-ready" in hypothesis
            else "entailment"
        )
        return {
            "predicted_relation": relation,
            "uncalibrated_model_scores": {
                "contradiction": 0.8 if relation == "contradiction" else 0.1,
                "entailment": 0.8 if relation == "entailment" else 0.1,
                "neutral": 0.8 if relation == "neutral" else 0.1,
            },
            "not_a_truth_probability": True,
            "not_authorized_to_support_claim": True,
        }


def patched_reader(monkeypatch, response=None, *, fail=False):
    calls = []

    def fetch(self, uri):
        calls.append(uri)
        if fail:
            raise RuntimeError("private source token must never leak")
        return observed() if response is None else response

    monkeypatch.setattr(AllowlistedHttpsSourceReader, "__call__", fetch)
    return AllowlistedHttpsSourceReader([s.SOURCE]), calls


def test_valid_single_source_observation_reuses_one_premise_for_all_three_claims(monkeypatch):
    reader, calls = patched_reader(monkeypatch)
    model = FakeModel()
    result = s.evaluate_live_observed_nli(reader=reader, model=model, now=AT)
    assert calls == [s.SOURCE]
    assert len(model.calls) == 3
    assert all(x[0] == s.STANDALONE_ANCHOR for x in model.calls)
    assert result["source_captures"] == 1
    assert result["capture_sha256"] == HASH
    assert result["selected_source_unit_sha256"] == UNIT_SHA
    assert result["fixed_developer_claims_evaluated"] == 3
    assert [x["neural_shadow_prediction"] for x in result["cases"]] == [
        "entailment", "contradiction", "neutral"
    ]
    assert [x["deterministic_text_relation"] for x in result["cases"]] == [
        "aligned", "contradicted", "insufficient"
    ]
    assert all(x["neural_may_promote_reality_state"] is False for x in result["cases"])
    assert result["model_semantic_accuracy_established"] is False
    assert result["neural_can_authorize_production_claim_support"] is False
    assert result["source_publisher_authorship_cryptographically_verified"] is False
    assert s.STANDALONE_ANCHOR not in json.dumps(result)
    assert BODY not in json.dumps(result)


@pytest.mark.parametrize("changes", [
    {"uri": "https://www.iana.org/domains/reserved"},
    {"content": ""},
    {"content": "Different publisher statement, not the preapproved observed assertion"},
    {"content": BODY + "\n" + s.STANDALONE_ANCHOR},
    {"content": "says " + s.STANDALONE_ANCHOR + " is disputed"},
    {"content": s.STANDALONE_ANCHOR + " other words"},
    {"content": s.STANDALONE_ANCHOR + "\n" + s.STANDALONE_ANCHOR},
    {"content": "a" * 100_000},
    {"capture_sha256": "not-hex"},
    {"capture_sha256": "0" * 63},
    {"capture_observed_at": "invalid-date"},
    {"capture_observed_at": "2026-10-13T14:00:00+00:00"},
    {"capture_observed_at": "2026-10-13T12:00:00Z"},
    {"capture_observed_at": "2026-10-13T14:01:00Z"},
    {"observed_quote_unit_sha256": [UNIT_SHA]},
    {"observed_quote_unit_sha256": "not-list"},
    {"observed_quote_unit_sha256": ["invalid"]},
    {"observed_quote_unit_sha256": ["0" * 64, "0" * 64]},
])
def test_bad_source_receipt_or_nonunique_quote_refuses_without_running_model(
    monkeypatch, changes
):
    response = observed(**changes)
    reader, calls = patched_reader(monkeypatch, response)
    model = FakeModel()
    with pytest.raises(s.ObservedNLIError):
        s.evaluate_live_observed_nli(reader=reader, model=model, now=AT)
    assert calls == [s.SOURCE]
    assert model.calls == []


def test_wrong_allowlisted_source_not_fetched(monkeypatch):
    reader, calls = patched_reader(monkeypatch)
    reader = AllowlistedHttpsSourceReader(["https://www.iana.org/domains/reserved"])
    model = FakeModel()
    with pytest.raises(s.ObservedNLIError, match="unapproved_source_reader"):
        s.evaluate_live_observed_nli(reader=reader, model=model, now=AT)
    assert calls == []
    assert model.calls == []


def test_two_allowed_urls_not_accepted_even_when_target_is_one_of_them(monkeypatch):
    reader, calls = patched_reader(monkeypatch)
    reader = AllowlistedHttpsSourceReader([s.SOURCE, "https://www.iana.org/domains/reserved"])
    with pytest.raises(s.ObservedNLIError, match="unapproved_source_reader"):
        s.evaluate_live_observed_nli(reader=reader, model=FakeModel(), now=AT)
    assert calls == []


def test_source_reader_exception_is_sanitized(monkeypatch, capsys):
    reader, calls = patched_reader(monkeypatch, fail=True)
    with pytest.raises(s.ObservedNLIError, match="original_source_capture_unavailable"):
        s.evaluate_live_observed_nli(reader=reader, model=FakeModel(), now=AT)
    assert calls == [s.SOURCE]
    monkeypatch.setattr(s, "run_live", lambda **kwargs: (_ for _ in ()).throw(
        RuntimeError("private-publisher-secret")
    ))
    assert s.main(["--live"]) == 1
    assert "private-publisher-secret" not in capsys.readouterr().out


@pytest.mark.parametrize("bad", [
    {"predicted_relation": "supported"},
    {"predicted_relation": "entailment", "not_a_truth_probability": True,
     "not_authorized_to_support_claim": False},
    {"predicted_relation": "entailment", "not_a_truth_probability": True,
     "not_authorized_to_support_claim": True,
     "uncalibrated_model_scores": {"entailment": 1.0}},
    {"predicted_relation": "entailment", "not_a_truth_probability": True,
     "not_authorized_to_support_claim": True,
     "uncalibrated_model_scores": {
         "entailment": 0.9, "contradiction": 0.9, "neutral": 0.5
     }},
    {"predicted_relation": "entailment", "not_a_truth_probability": True,
     "not_authorized_to_support_claim": True,
     "uncalibrated_model_scores": {
         "entailment": float("nan"), "contradiction": 0.0, "neutral": 0.0
     }},
    {"predicted_relation": "entailment", "not_a_truth_probability": True,
     "not_authorized_to_support_claim": True,
     "uncalibrated_model_scores": {
         "entailment": True, "contradiction": 0.0, "neutral": 0.0
     }},
    ["entailment"],
])
def test_invalid_neural_output_never_promotes_factual_support(monkeypatch, bad):
    reader, _ = patched_reader(monkeypatch)
    model = FakeModel(invalid=bad)
    with pytest.raises(s.ObservedNLIError):
        s.evaluate_live_observed_nli(reader=reader, model=model, now=AT)


def test_invalid_or_naive_clock_rejected(monkeypatch):
    reader, calls = patched_reader(monkeypatch)
    with pytest.raises(s.ObservedNLIError, match="clock_invalid"):
        s.evaluate_live_observed_nli(reader=reader, model=FakeModel(),
                                     now=datetime(2026, 10, 13, 14, 0))
    assert calls == [s.SOURCE]


def test_default_cli_never_performs_network_or_loads_model(monkeypatch, capsys):
    calls = []
    monkeypatch.setattr(s, "run_live", lambda **kwargs: calls.append("network"))
    with pytest.raises(SystemExit):
        s.main([])
    assert calls == []
    assert "--live required" in capsys.readouterr().err


def test_internal_model_exception_is_sanitized(monkeypatch):
    reader, _ = patched_reader(monkeypatch)
    class Bad:
        def predict(self, *args):
            raise ValueError("sensitive-neural-internals")
    with pytest.raises(s.ObservedNLIError, match="neural_inference_unavailable"):
        s.evaluate_live_observed_nli(reader=reader, model=Bad(), now=AT)


def test_source_observation_requires_real_reader_class(monkeypatch):
    class ArbitraryNetwork:
        _allowed = frozenset({s.SOURCE})
        def __call__(self, *args):
            raise AssertionError("not authorized")
    with pytest.raises(s.ObservedNLIError, match="unapproved_source_reader"):
        s.evaluate_live_observed_nli(reader=ArbitraryNetwork(), model=FakeModel(), now=AT)
