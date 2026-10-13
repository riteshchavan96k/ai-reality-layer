"""Step240 actual authenticated FastAPI and tampered neural-source handoff tests."""

from copy import deepcopy
from datetime import datetime, timezone
from hashlib import sha256
import json

import pytest
from fastapi.testclient import TestClient

from backend.app.api.original_source_claim import OriginalSourceClaimRequest
from backend.app.integrations.ai_claim_gate import check_claim_with_api
from backend.app.integrations.semantic_veto import (
    _valid_neural_result, check_claim_with_semantic_veto,
)
from backend.app.main import app
from backend.app.reality.allowlisted_https_source_reader import AllowlistedHttpsSourceReader

SOURCE = "https://www.python.org/downloads/release/python-3130/"
TEXT = "This is the stable release of Python 3.13.0"
TOKEN = "step240-tiny-authenticated-integration-secret-value"


def request(text="Python 3.13.0 is a stable release.", url=SOURCE):
    return OriginalSourceClaimRequest(
        claim_text=text, source_uri=url, entity="Python 3.13.0"
    )


class NeuralModel:
    def __init__(self, label="entailment", *, malformed=None, raises=False):
        self.calls = []
        self.label = label
        self.malformed = malformed
        self.raises = raises

    def predict(self, premise, hypothesis):
        self.calls.append((premise, hypothesis))
        if self.raises:
            raise RuntimeError("sensitive model error")
        if self.malformed is not None:
            return self.malformed
        scores = {key: .1 for key in ("entailment", "neutral", "contradiction")}
        scores[self.label] = .8
        return {
            "predicted_relation": self.label,
            "uncalibrated_model_scores": scores,
            "not_a_truth_probability": True,
            "not_authorized_to_support_claim": True,
        }


@pytest.fixture
def api(monkeypatch):
    monkeypatch.setenv("ARL_RUNTIME_MODE", "pilot")
    monkeypatch.setenv("ARL_PILOT_BEARER_TOKEN", TOKEN)
    monkeypatch.setenv("ARL_INDEPENDENT_SOURCE_ALLOWED_URLS", json.dumps([SOURCE]))
    visits = []

    def source_reader(self, uri):
        visits.append(uri)
        return {
            "uri": uri,
            "content": TEXT,
            "capture_sha256": sha256(TEXT.encode()).hexdigest(),
            "capture_observed_at": datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"),
            "observed_quote_unit_sha256": [],
        }

    monkeypatch.setattr(AllowlistedHttpsSourceReader, "__call__", source_reader)
    with TestClient(app) as client:
        yield client, visits


def server_response(api, req=None):
    client, _ = api
    req = req or request()
    response = client.post(
        "/api/v1/reality-state/claim",
        json=req.model_dump(mode="json"),
        headers={"Authorization": "Bearer " + TOKEN},
    )
    assert response.status_code == 200
    return response.json()


class Response:
    status_code = 200
    headers = {"content-type": "application/json"}

    def __init__(self, payload, *, status=200, headers=None):
        self.payload = payload
        self.status_code = status
        self.headers = {"content-type": "application/json"} if headers is None else headers
        self.content = json.dumps(payload).encode()

    def json(self):
        return deepcopy(self.payload)


class Client:
    def __init__(self, payload, *, status=200, headers=None):
        self.reply = Response(payload, status=status, headers=headers)
        self.calls = []

    def post(self, path, **kwargs):
        self.calls.append((path, kwargs))
        return self.reply


def test_authenticated_server_handoff_is_same_original_capture_and_source(api):
    client, calls = api
    result = server_response(api)
    evidence = result["source_evidence"]
    assert evidence["text"] == TEXT
    assert evidence["text_sha256"] == sha256(TEXT.encode("utf-8")).hexdigest()
    assurance = result["reality_state"]["evidence"]["independent_source_text_assurance"]
    original = assurance["sources"][0]
    assert evidence["source_capture_sha256"] == original["capture_sha256"]
    assert evidence["source_capture_observed_at"] == original["capture_observed_at"]
    assert calls == [SOURCE]


def test_one_authenticated_request_produces_model_veto_check_without_extra_capture(api):
    client, calls = api
    model = NeuralModel()
    outcome = check_claim_with_semantic_veto(client, TOKEN, request(), model=model)
    assert outcome.decision == "bounded_supported"
    assert outcome.may_use_as_bounded_evidence is True
    assert outcome.reason_code == "neural_entailment_agrees"
    assert outcome.source_ref == SOURCE
    assert outcome.selected_text_sha256 == sha256(TEXT.encode()).hexdigest()
    assert outcome.semantic_truth_verified is False
    assert outcome.neural_authorized_to_upgrade_claims is False
    assert model.calls == [(TEXT, "Python 3.13.0 is a stable release.")]
    assert calls == [SOURCE]
    assert TOKEN not in repr(outcome)
    assert TEXT not in repr(outcome)


@pytest.mark.parametrize("label", ["neutral", "contradiction"])
def test_neural_non_entailment_may_only_veto_supported(api, label):
    client, calls = api
    model = NeuralModel(label)
    result = check_claim_with_semantic_veto(client, TOKEN, request(), model=model)
    assert result.decision == "abstain"
    assert result.may_use_as_bounded_evidence is False
    assert result.reason_code == "neural_veto_nonentailment"
    assert len(model.calls) == 1
    assert calls == [SOURCE]


def test_source_contradiction_cannot_be_upgraded_or_rechecked_by_model(api):
    client, calls = api
    model = NeuralModel("entailment")
    result = check_claim_with_semantic_veto(
        client, TOKEN, request("Python 3.13.0 is not a stable release."), model=model
    )
    assert result.decision == "bounded_contradicted"
    assert result.may_use_as_bounded_evidence is False
    assert result.reason_code == "source_bounded_contradiction"
    assert model.calls == []
    assert calls == [SOURCE]


@pytest.mark.parametrize("claim", [
    "Python 3.13.0 was released on January 1, 1900.",
    "Python 3.13.0 is a production-ready release.",
    "This claim is suspicious, might be stable.",
])
def test_unsupported_grammar_cannot_be_promoted_by_an_entailing_model(api, claim):
    client, _ = api
    model = NeuralModel("entailment")
    result = check_claim_with_semantic_veto(client, TOKEN, request(claim), model=model)
    assert result.decision == "abstain"
    assert result.may_use_as_bounded_evidence is False
    assert model.calls == []


def test_unallowed_source_never_fetched_or_upgraded(api):
    client, calls = api
    model = NeuralModel()
    result = check_claim_with_semantic_veto(
        client, TOKEN, request(url="https://www.python.org/unapproved/"), model=model
    )
    assert result.decision == "abstain"
    assert calls == []
    assert model.calls == []


def test_invalid_auth_never_fetches_source_or_runs_model(api):
    client, calls = api
    model = NeuralModel()
    result = check_claim_with_semantic_veto(client, TOKEN + "wrong", request(), model=model)
    assert result.decision == "abstain"
    assert result.reason_code == "api_unavailable_or_invalid"
    assert model.calls == []
    assert calls == []


@pytest.mark.parametrize("edit", [
    lambda p: p["source_evidence"].update({"text": "forged source says the claim is true"}),
    lambda p: p["source_evidence"].update({"text_sha256": "0" * 64}),
    lambda p: p["source_evidence"].update({"source_capture_sha256": "0" * 64}),
    lambda p: p["source_evidence"].update({"source_capture_observed_at": "1970-01-01T00:00:00Z"}),
    lambda p: p.update({"source_evidence": None}),
    lambda p: p["source_evidence"].update({"text": "X" * 501}),
    lambda p: p["source_evidence"].update({"text": TEXT + "\nnew line"}),
    lambda p: p["source_evidence"].update({"extra_field": "wrong"}),
    lambda p: p.update({"request_binding_sha256": "0" * 64}),
    lambda p: p.update({"source_ref": "https://www.iana.org/domains/reserved"}),
    lambda p: p["reality_state"].update({"status": "uncertain"}),
    lambda p: p["reality_state"]["evidence"]["claim_alignment"].update({"status": "insufficient"}),
])
def test_tampering_never_yields_supported_or_model_call(api, edit):
    payload = server_response(api)
    edited = deepcopy(payload)
    edit(edited)
    fake = Client(edited)
    model = NeuralModel()
    result = check_claim_with_semantic_veto(fake, TOKEN, request(), model=model)
    assert result.decision == "abstain"
    assert result.may_use_as_bounded_evidence is False
    assert model.calls == []
    assert len(fake.calls) == 1


@pytest.mark.parametrize("malformed", [
    {},
    {"predicted_relation": "supported"},
    {"predicted_relation": "entailment", "not_a_truth_probability": True,
     "not_authorized_to_support_claim": False},
    {"predicted_relation": "entailment", "not_a_truth_probability": True,
     "not_authorized_to_support_claim": True,
     "uncalibrated_model_scores": {"entailment": 1.0}},
    {"predicted_relation": "neutral", "not_a_truth_probability": True,
     "not_authorized_to_support_claim": True,
     "uncalibrated_model_scores": {"entailment": .8, "neutral": .1, "contradiction": .1}},
    {"predicted_relation": "entailment", "not_a_truth_probability": True,
     "not_authorized_to_support_claim": True,
     "uncalibrated_model_scores": {"entailment": float("nan"), "neutral": .1, "contradiction": .9}},
    {"predicted_relation": "entailment", "not_a_truth_probability": True,
     "not_authorized_to_support_claim": True,
     "uncalibrated_model_scores": {"entailment": .8, "neutral": True, "contradiction": .1}},
    {"predicted_relation": "entailment", "not_a_truth_probability": True,
     "not_authorized_to_support_claim": True,
     "uncalibrated_model_scores": {"entailment": .8, "neutral": .1, "contradiction": .1},
     "factual_truth_verified": True},
])
def test_malformed_or_unauthorized_model_decision_refuses(api, malformed):
    payload = server_response(api)
    model = NeuralModel(malformed=malformed)
    result = check_claim_with_semantic_veto(Client(payload), TOKEN, request(), model=model)
    assert result.decision == "abstain"
    assert result.may_use_as_bounded_evidence is False
    assert len(model.calls) == 1


def test_model_missing_exception_and_noncallable_always_abstain(api):
    payload = server_response(api)
    for model in [None, object(), NeuralModel(raises=True)]:
        result = check_claim_with_semantic_veto(
            Client(payload), TOKEN, request(), model=model
        )
        assert result.decision == "abstain"
        assert result.may_use_as_bounded_evidence is False


@pytest.mark.parametrize("status,content_type", [
    (401, "application/json"), (403, "application/json"),
    (500, "application/json"), (200, "text/html"),
])
def test_api_invalid_status_or_mime_abstains(api, status, content_type):
    payload = server_response(api)
    model = NeuralModel()
    result = check_claim_with_semantic_veto(
        Client(payload, status=status, headers={"content-type": content_type}),
        TOKEN, request(), model=model
    )
    assert result.decision == "abstain"
    assert model.calls == []


def test_original_step235_consumer_unmodified_and_remains_safe(api):
    client, _ = api
    decision = check_claim_with_api(client, TOKEN, request())
    assert decision.decision == "bounded_supported"
    assert decision.semantic_truth_verified is False
    assert decision.publisher_authorship_verified is False


def test_no_production_model_download_or_import_required():
    from backend.app.models.catalog import MODEL_CATALOG
    assert list(MODEL_CATALOG) == ["mock-model"]
    from backend.app.integrations import semantic_veto as module
    assert "step237_nli_shadow" not in module.__dict__


def test_non_request_input_refused_before_any_transport():
    fake = Client({})
    with pytest.raises(TypeError):
        check_claim_with_semantic_veto(fake, TOKEN, {}, model=NeuralModel())
    assert fake.calls == []


def test_legacy_source_response_does_not_grant_neural_support(api):
    payload = server_response(api)
    payload.pop("source_evidence")
    model = NeuralModel()
    result = check_claim_with_semantic_veto(Client(payload), TOKEN, request(), model=model)
    assert result.decision == "abstain"
    assert model.calls == []
