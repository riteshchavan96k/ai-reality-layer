from backend.app.reality.grounding_context_contract import GroundingContext
from backend.app.reality.grounding_context_normalizer import GroundingContextNormalizer


def test_normalized_mapping_preserves_execution_flag() -> None:
    context = GroundingContextNormalizer.normalize({"status":"not_available","task":"Task","content":None,"sources":[],"source_count":0,"grounding_executed":False})
    assert context.to_dict()["grounding_executed"] is False


def test_typed_context_round_trip() -> None:
    context = GroundingContext.ready_result("Task", "Content", [])
    assert GroundingContextNormalizer.normalize(context).to_dict() == context.to_dict()
