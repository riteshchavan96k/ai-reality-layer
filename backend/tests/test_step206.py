"""Step 206 — canonical structured claim representation foundation."""

import pytest

from backend.app.orchestrator.orchestrator import (
    build_reality_state_from_evidence,
)
from backend.app.reality.claim_conflict_detector import ClaimConflictDetector
from backend.app.reality.claim_evidence_linker import ClaimEvidenceLinker
from backend.app.reality.claim_extraction import (
    ClaimExtractionResult,
    EvidenceClaim,
)
from backend.app.reality.claim_extraction_normalizer import (
    ClaimExtractionResultNormalizer,
)
from backend.app.reality.claim_extractor import EvidenceClaimExtractor
from backend.app.reality.claim_semantic_structure import (
    ClaimSemanticStructure,
    MAX_CLAIM_SEMANTIC_FIELD_CHARS,
)


SOURCE_A = "https://example.test/a"
SOURCE_B = "https://example.test/b"


def _structured_claim(text: str = "Company X launched Feature A.") -> EvidenceClaim:
    return EvidenceClaim(
        text=text,
        source_refs=(SOURCE_A,),
        semantic_structure=ClaimSemanticStructure.structured(
            subject="Company X",
            predicate="launched",
            object="Feature A",
            structuring_method="test_semantic_structurer",
        ),
    )


def test_unstructured_semantic_structure_is_explicit():
    structure = ClaimSemanticStructure.unstructured()

    assert structure.to_dict() == {
        "status": "unstructured",
        "subject": None,
        "predicate": None,
        "object": None,
        "structuring_method": "not_attempted",
        "reason": "semantic_structuring_not_attempted",
    }


def test_structured_semantic_structure_is_canonicalized():
    structure = ClaimSemanticStructure.structured(
        subject="  Company X  ",
        predicate="  launched  ",
        object="  Feature A  ",
        structuring_method="  test_semantic_structurer  ",
    )

    assert structure.to_dict() == {
        "status": "structured",
        "subject": "Company X",
        "predicate": "launched",
        "object": "Feature A",
        "structuring_method": "test_semantic_structurer",
        "reason": None,
    }


@pytest.mark.parametrize(
    ("field", "value", "match"),
    [
        ("subject", "", "claim subject must be a non-empty string"),
        ("predicate", "   ", "claim predicate must be a non-empty string"),
        ("object", None, "claim object must be a non-empty string"),
        (
            "subject",
            "x" * (MAX_CLAIM_SEMANTIC_FIELD_CHARS + 1),
            "claim subject must not exceed",
        ),
    ],
)
def test_structured_semantic_structure_rejects_invalid_parts(
    field,
    value,
    match,
):
    kwargs = {
        "subject": "Company X",
        "predicate": "launched",
        "object": "Feature A",
        "structuring_method": "test_semantic_structurer",
    }
    kwargs[field] = value

    with pytest.raises(ValueError, match=match):
        ClaimSemanticStructure.structured(**kwargs)


def test_structured_semantic_structure_rejects_not_attempted_method():
    with pytest.raises(
        ValueError,
        match="structured claim requires a non-empty structuring method",
    ):
        ClaimSemanticStructure.structured(
            subject="Company X",
            predicate="launched",
            object="Feature A",
            structuring_method="not_attempted",
        )


def test_structured_semantic_structure_rejects_reason():
    with pytest.raises(
        ValueError,
        match="structured claim semantic structure cannot contain a reason",
    ):
        ClaimSemanticStructure(
            status="structured",
            subject="Company X",
            predicate="launched",
            object="Feature A",
            structuring_method="test_semantic_structurer",
            reason="unexpected",
        )


def test_unstructured_semantic_structure_rejects_semantic_parts():
    with pytest.raises(
        ValueError,
        match="unstructured claim cannot contain subject",
    ):
        ClaimSemanticStructure(
            status="unstructured",
            subject="Company X",
            predicate=None,
            object=None,
            structuring_method="not_attempted",
            reason="semantic_structuring_not_attempted",
        )


def test_unstructured_semantic_structure_requires_reason():
    with pytest.raises(
        ValueError,
        match="unstructured claim requires a non-empty reason",
    ):
        ClaimSemanticStructure(
            status="unstructured",
            subject=None,
            predicate=None,
            object=None,
            structuring_method="not_attempted",
            reason=None,
        )


def test_legacy_evidence_claim_defaults_to_explicit_unstructured_state():
    claim = EvidenceClaim(
        text="Company X launched Feature A.",
        source_refs=(SOURCE_A,),
    )

    assert claim.semantic_structure.status == "unstructured"
    assert claim.semantic_structure.reason == "semantic_structuring_not_attempted"
    assert claim.to_dict()["semantic_structure"]["subject"] is None


def test_evidence_claim_preserves_structured_semantics():
    claim = _structured_claim()

    assert claim.semantic_structure.status == "structured"
    assert claim.semantic_structure.subject == "Company X"
    assert claim.to_dict()["semantic_structure"]["predicate"] == "launched"


def test_legacy_claim_mapping_without_semantics_normalizes_safely():
    result = ClaimExtractionResultNormalizer.normalize(
        {
            "status": "usable",
            "claims": [
                {
                    "text": "Company X launched Feature A.",
                    "source_refs": [SOURCE_A],
                    "extraction_method": "deterministic_sentence_split",
                }
            ],
            "source_count": 1,
            "extraction_executed": True,
            "reason": None,
        }
    )

    claim = result.claims[0]
    assert claim.semantic_structure.status == "unstructured"
    assert claim.semantic_structure.subject is None


def test_mapping_with_structured_semantics_round_trips():
    claim = _structured_claim()
    result = ClaimExtractionResult.validate(
        {
            "status": "usable",
            "claims": [claim.to_dict()],
            "source_count": 1,
            "extraction_executed": True,
            "reason": None,
        }
    )

    assert result.claims[0].semantic_structure == claim.semantic_structure
    assert result.to_dict()["claims"][0]["semantic_structure"]["object"] == (
        "Feature A"
    )


def test_malformed_nested_semantic_structure_is_rejected():
    raw = _structured_claim().to_dict()
    del raw["semantic_structure"]["predicate"]

    with pytest.raises(
        ValueError,
        match="claim semantic structure is missing required fields",
    ):
        ClaimExtractionResult.validate(
            {
                "status": "usable",
                "claims": [raw],
                "source_count": 1,
                "extraction_executed": True,
                "reason": None,
            }
        )


def test_current_sentence_extractor_marks_claims_unstructured():
    result = EvidenceClaimExtractor().extract_result(
        {
            "status": "usable",
            "sources": [{"uri": SOURCE_A}],
            "content": "Company X launched Feature A.",
        }
    )

    assert result.status == "usable"
    claim = result.claims[0]
    assert claim.text == "Company X launched Feature A."
    assert claim.semantic_structure.status == "unstructured"
    assert claim.semantic_structure.structuring_method == "not_attempted"
    assert claim.semantic_structure.reason == "semantic_structuring_not_attempted"


def test_duplicate_claim_deduplication_preserves_semantic_state():
    result = EvidenceClaimExtractor().extract_result(
        {
            "status": "completed",
            "sources": [
                {
                    "uri": SOURCE_A,
                    "content": "Shared claim.",
                },
                {
                    "uri": SOURCE_B,
                    "content": "Shared claim.",
                },
            ],
            "content": "Shared claim.\n\nShared claim.",
        }
    )

    assert result.status == "usable"
    assert len(result.claims) == 1
    assert result.claims[0].source_refs == (SOURCE_A, SOURCE_B)
    assert result.claims[0].semantic_structure.status == "unstructured"


def test_linker_mapping_reconstruction_preserves_structured_semantics():
    claim = _structured_claim()
    reconstructed = ClaimEvidenceLinker._claim_result_from_mapping(
        {
            "status": "usable",
            "claims": [claim.to_dict()],
            "source_count": 1,
            "extraction_executed": True,
            "reason": None,
        }
    )

    assert reconstructed.claims[0].semantic_structure == (
        claim.semantic_structure
    )


def test_conflict_mapping_reconstruction_preserves_structured_semantics():
    claim = _structured_claim()
    reconstructed = ClaimConflictDetector._from_mapping(
        {
            "status": "usable",
            "claims": [claim.to_dict()],
            "source_count": 1,
            "extraction_executed": True,
            "reason": None,
        }
    )

    assert reconstructed.claims[0].semantic_structure == (
        claim.semantic_structure
    )


def test_structured_claim_remains_compatible_with_evidence_linking():
    extraction = ClaimExtractionResult.usable_result(
        (_structured_claim(),),
        source_count=1,
    )

    linking = ClaimEvidenceLinker().link_result(
        extraction,
        {
            "status": "usable",
            "sources": [{"uri": SOURCE_A}],
        },
    )

    assert linking.status == "usable"
    assert linking.linked_claim_count == 1
    assert linking.links[0].claim_text == "Company X launched Feature A."


def test_structured_claims_do_not_change_deterministic_conflict_policy():
    positive = _structured_claim("Company X is operating.")
    negative = EvidenceClaim(
        text="not Company X is operating.",
        source_refs=(SOURCE_B,),
        semantic_structure=ClaimSemanticStructure.structured(
            subject="Company X",
            predicate="operating",
            object="false",
            structuring_method="test_semantic_structurer",
        ),
    )
    extraction = ClaimExtractionResult.usable_result(
        (positive, negative),
        source_count=2,
    )

    conflicts = ClaimConflictDetector().detect_result(extraction)

    assert conflicts.status == "usable"
    assert conflicts.conflict_count == 1


def test_reality_state_exposes_explicit_unstructured_claim_semantics():
    state = build_reality_state_from_evidence(
        "What is the current status of Company X?",
        [
            {
                "uri": SOURCE_A,
                "content": "Company X launched Feature A.",
            }
        ],
        entity="Company X",
    )

    semantic = state["claims"]["claims"][0]["semantic_structure"]
    assert semantic == {
        "status": "unstructured",
        "subject": None,
        "predicate": None,
        "object": None,
        "structuring_method": "not_attempted",
        "reason": "semantic_structuring_not_attempted",
    }


def test_explicit_reality_entity_does_not_auto_fill_claim_subject():
    state = build_reality_state_from_evidence(
        "What is the current status?",
        [
            {
                "uri": SOURCE_A,
                "content": "Feature A is available.",
            }
        ],
        entity="Company X",
    )

    assert state["entity"]["name"] == "Company X"
    claim = state["claims"]["claims"][0]
    assert claim["semantic_structure"]["status"] == "unstructured"
    assert claim["semantic_structure"]["subject"] is None


def test_claim_semantics_do_not_change_existing_text_or_lineage():
    state = build_reality_state_from_evidence(
        "What changed?",
        [
            {"uri": SOURCE_A, "content": "Shared claim. Unique A."},
            {"uri": SOURCE_B, "content": "Shared claim. Unique B."},
        ],
    )

    by_text = {
        claim["text"]: claim
        for claim in state["claims"]["claims"]
    }
    assert by_text["Shared claim."]["source_refs"] == [SOURCE_A, SOURCE_B]
    assert by_text["Unique A."]["source_refs"] == [SOURCE_A]
    assert by_text["Unique B."]["source_refs"] == [SOURCE_B]
    assert all(
        claim["semantic_structure"]["status"] == "unstructured"
        for claim in by_text.values()
    )
