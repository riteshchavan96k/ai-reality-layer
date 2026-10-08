"""Step 204 — canonical first-class Reality Entity foundation."""

import pytest

from backend.app.api.evidence_reality_state import EvidenceRealityStateRequest
from backend.app.api.reality_state import (
    RealityEntityResponse,
    RealityStateRequest,
    RealityStateResponse,
)
from backend.app.main import app, reality_state, reality_state_from_evidence
from backend.app.orchestrator.orchestrator import (
    build_reality_state,
    build_reality_state_from_evidence,
)
from backend.app.reality.reality_entity import (
    MAX_REALITY_ENTITY_NAME_CHARS,
    RealityEntity,
)
from backend.app.reality.reality_state import RealityState
from backend.app.reality.retrieval_result import RetrievalResultContract


ENTITY = "Company X"
SOURCE = "https://example.test/company-x"
CONTENT = "Company X launched Feature A today."


class _CompletedRetrievalEngine:
    def retrieve(self, contract):
        return RetrievalResultContract.completed(
            contract["request"],
            provider="test-provider",
            sources=[
                {
                    "title": "Company X update",
                    "uri": SOURCE,
                }
            ],
            content=CONTENT,
        )


def _document():
    return {
        "title": "Company X update",
        "uri": SOURCE,
        "content": CONTENT,
    }


def _legacy_state_mapping():
    return {
        "status": "uncertain",
        "task": "What is the current status of Company X?",
        "evidence": {},
        "claims": {},
        "claim_evidence_linking": {},
        "source_provenance": {},
        "source_observation": {},
        "freshness": {},
        "conflicts": {},
        "confidence_signals": {},
        "assembly_method": "deterministic_signal_snapshot",
        "reason": None,
    }


def test_explicit_entity_is_canonicalized():
    entity = RealityEntity.specified("  Company X  ")

    assert entity.status == "specified"
    assert entity.name == ENTITY
    assert entity.identification_method == "explicit_input"
    assert entity.to_dict() == {
        "status": "specified",
        "name": ENTITY,
        "identification_method": "explicit_input",
    }


def test_unspecified_entity_is_explicit():
    entity = RealityEntity.unspecified()

    assert entity.to_dict() == {
        "status": "unspecified",
        "name": None,
        "identification_method": "not_provided",
    }


def test_entity_validate_accepts_string_mapping_and_typed_contract():
    typed = RealityEntity.specified(ENTITY)

    assert RealityEntity.validate(typed) is typed
    assert RealityEntity.validate(ENTITY) == typed
    assert RealityEntity.validate(typed.to_dict()) == typed
    assert RealityEntity.validate(None) == RealityEntity.unspecified()


@pytest.mark.parametrize(
    ("value", "match"),
    [
        ("   ", "entity name must be a non-empty string"),
        (
            "x" * (MAX_REALITY_ENTITY_NAME_CHARS + 1),
            "entity name must not exceed",
        ),
    ],
)
def test_explicit_entity_name_rejects_invalid_values(value, match):
    with pytest.raises(ValueError, match=match):
        RealityEntity.specified(value)


def test_entity_contract_rejects_inconsistent_state():
    with pytest.raises(
        ValueError,
        match="specified entity requires explicit_input identification method",
    ):
        RealityEntity(
            status="specified",
            name=ENTITY,
            identification_method="not_provided",
        )

    with pytest.raises(
        ValueError,
        match="unspecified entity cannot contain a name",
    ):
        RealityEntity(
            status="unspecified",
            name=ENTITY,
            identification_method="not_provided",
        )


def test_reality_state_legacy_mapping_defaults_entity_to_unspecified():
    state = RealityState.validate(_legacy_state_mapping())

    assert state.entity == RealityEntity.unspecified()
    assert state.to_dict()["entity"] == {
        "status": "unspecified",
        "name": None,
        "identification_method": "not_provided",
    }


def test_reality_state_mapping_preserves_explicit_entity():
    raw = {
        **_legacy_state_mapping(),
        "entity": RealityEntity.specified(ENTITY).to_dict(),
    }

    state = RealityState.validate(raw)

    assert state.entity.name == ENTITY
    assert state.to_dict()["entity"]["status"] == "specified"


def test_retrieval_backed_reality_state_preserves_explicit_entity():
    state = build_reality_state(
        "What is the current status?",
        retrieval_engine=_CompletedRetrievalEngine(),
        entity="  Company X  ",
    )

    assert state["entity"] == {
        "status": "specified",
        "name": ENTITY,
        "identification_method": "explicit_input",
    }
    assert state["evidence"]["status"] == "completed"


def test_retrieval_backed_reality_state_does_not_infer_entity_from_task():
    state = build_reality_state(
        "What is the current status of Company X?",
        retrieval_engine=_CompletedRetrievalEngine(),
    )

    assert state["entity"] == {
        "status": "unspecified",
        "name": None,
        "identification_method": "not_provided",
    }


def test_submitted_evidence_reality_state_preserves_explicit_entity():
    state = build_reality_state_from_evidence(
        "What is the current status?",
        [_document()],
        entity=ENTITY,
    )

    assert state["entity"] == {
        "status": "specified",
        "name": ENTITY,
        "identification_method": "explicit_input",
    }
    assert state["evidence"]["status"] == "completed"


def test_submitted_evidence_without_entity_remains_unspecified():
    state = build_reality_state_from_evidence(
        "What is the current status of Company X?",
        [_document()],
    )

    assert state["entity"]["status"] == "unspecified"
    assert state["entity"]["name"] is None


def test_reality_state_request_accepts_and_normalizes_optional_entity():
    request = RealityStateRequest(
        task="What is the current status?",
        entity="  Company X  ",
    )

    assert request.entity == ENTITY


def test_submitted_evidence_request_accepts_and_normalizes_optional_entity():
    request = EvidenceRealityStateRequest(
        task="What is the current status?",
        entity="  Company X  ",
        documents=[_document()],
    )

    assert request.entity == ENTITY


@pytest.mark.parametrize("request_type", [RealityStateRequest, EvidenceRealityStateRequest])
def test_api_requests_reject_blank_entity(request_type):
    kwargs = {
        "task": "What is the current status?",
        "entity": "   ",
    }
    if request_type is EvidenceRealityStateRequest:
        kwargs["documents"] = [_document()]

    with pytest.raises(Exception, match="entity name must be a non-empty string"):
        request_type(**kwargs)


def test_api_request_rejects_oversized_entity():
    with pytest.raises(Exception):
        RealityStateRequest(
            task="What is the current status?",
            entity="x" * (MAX_REALITY_ENTITY_NAME_CHARS + 1),
        )


def test_retrieval_http_handler_threads_entity_to_snapshot():
    request = RealityStateRequest(
        task="What is the current status?",
        entity=ENTITY,
    )

    # The default unconfigured retrieval path may be unavailable/insufficient,
    # but entity identity must still survive the complete endpoint path.
    state = reality_state(request)

    assert state["entity"]["status"] == "specified"
    assert state["entity"]["name"] == ENTITY


def test_submitted_evidence_http_handler_threads_entity_to_snapshot():
    request = EvidenceRealityStateRequest(
        task="What is the current status?",
        entity=ENTITY,
        documents=[_document()],
    )

    state = reality_state_from_evidence(request)

    assert state["entity"]["status"] == "specified"
    assert state["entity"]["name"] == ENTITY


def test_reality_state_response_exposes_typed_entity_contract():
    field = RealityStateResponse.model_fields["entity"]

    assert field.annotation is RealityEntityResponse


def test_openapi_documents_entity_on_both_reality_state_requests_and_response():
    schema = app.openapi()

    retrieval_request = schema["components"]["schemas"]["RealityStateRequest"]
    evidence_request = schema["components"]["schemas"]["EvidenceRealityStateRequest"]
    response = schema["components"]["schemas"]["RealityStateResponse"]

    assert "entity" in retrieval_request["properties"]
    assert "entity" in evidence_request["properties"]
    assert response["properties"]["entity"]["$ref"].endswith(
        "/RealityEntityResponse"
    )


def test_existing_python_builder_call_without_entity_remains_compatible():
    state = build_reality_state(
        "What is the current status of Company X?",
        retrieval_engine=_CompletedRetrievalEngine(),
    )

    assert "entity" in state
    assert state["entity"]["status"] == "unspecified"
