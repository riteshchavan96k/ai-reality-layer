from typing import Any


SOURCE_TYPES = {
    "current_information": "live_web",
    "external_evidence": "web_or_official_source",
    "general_knowledge": "model_knowledge",
}


class RealitySourcePlanner:
    """Create a deterministic source plan from reality-context requirements."""

    def plan(self, reality_context: dict[str, Any]) -> dict[str, Any]:
        needs_current_info = reality_context.get("needs_current_info", False)
        needs_external_evidence = reality_context.get("needs_external_evidence", False)
        temporal_scope = reality_context.get("temporal_scope", "unspecified")

        if needs_current_info:
            source_type = SOURCE_TYPES["current_information"]
            priority = "required"
        elif needs_external_evidence:
            source_type = SOURCE_TYPES["external_evidence"]
            priority = "required"
        else:
            source_type = SOURCE_TYPES["general_knowledge"]
            priority = "optional"

        return {
            "source_type": source_type,
            "priority": priority,
            "temporal_scope": temporal_scope,
            "requires_retrieval": needs_current_info or needs_external_evidence,
            "status": "planned",
        }
