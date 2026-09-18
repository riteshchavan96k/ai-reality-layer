import pytest

from backend.app.reality.source_planner import RealitySourcePlanner


def test_current_information_requires_retrieval():
    plan = RealitySourcePlanner().plan(
        {
            "needs_current_info": True,
            "needs_external_evidence": False,
            "temporal_scope": "current",
        }
    )

    assert plan["source_type"] == "live_web"
    assert plan["requires_retrieval"] is True
    assert plan["priority"] == "required"


def test_external_evidence_requires_retrieval():
    plan = RealitySourcePlanner().plan(
        {
            "needs_current_info": False,
            "needs_external_evidence": True,
            "temporal_scope": "historical",
        }
    )

    assert plan["source_type"] == "web_or_official_source"
    assert plan["requires_retrieval"] is True


def test_general_knowledge_does_not_require_retrieval():
    plan = RealitySourcePlanner().plan(
        {
            "needs_current_info": False,
            "needs_external_evidence": False,
            "temporal_scope": "unspecified",
        }
    )

    assert plan["source_type"] == "model_knowledge"
    assert plan["requires_retrieval"] is False


def test_current_information_takes_priority_when_both_flags_are_true():
    plan = RealitySourcePlanner().plan(
        {
            "needs_current_info": True,
            "needs_external_evidence": True,
            "temporal_scope": "current",
        }
    )

    assert plan["source_type"] == "live_web"
    assert plan["requires_retrieval"] is True
