from typing import Any


CURRENT_SIGNALS = (
    "current",
    "currently",
    "latest",
    "today",
    "now",
    "recent",
    "recently",
    "this week",
    "this month",
    "this year",
)

EXTERNAL_EVIDENCE_SIGNALS = (
    "news",
    "price",
    "stock",
    "weather",
    "score",
    "schedule",
    "market",
    "live",
    "official",
    "source",
    "sources",
    "citation",
    "citations",
)


class RealityContextRequirementDetector:
    """Deterministically identify when a task needs external or current-world context."""

    def detect(self, task: str) -> dict[str, Any]:
        normalized = task.lower()

        current_signals = [
            signal for signal in CURRENT_SIGNALS if signal in normalized
        ]
        evidence_signals = [
            signal for signal in EXTERNAL_EVIDENCE_SIGNALS if signal in normalized
        ]

        needs_current_info = bool(current_signals)
        needs_external_evidence = bool(evidence_signals) or needs_current_info

        if needs_current_info:
            temporal_scope = "current"
        else:
            temporal_scope = "unspecified"

        if needs_external_evidence:
            status = "required"
        else:
            status = "not_required"

        return {
            "needs_current_info": needs_current_info,
            "needs_external_evidence": needs_external_evidence,
            "temporal_scope": temporal_scope,
            "current_signals": current_signals,
            "evidence_signals": evidence_signals,
            "status": status,
        }
