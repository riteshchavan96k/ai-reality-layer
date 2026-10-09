from typing import Any

from backend.app.reality.confidence_signal_normalizer import RealityConfidenceSignalResultNormalizer
from backend.app.reality.confidence_signals import RealityConfidenceSignalResult
from backend.app.reality.entity_relevance import explicit_entity_link_alignment
from backend.app.reality.reality_entity import RealityEntity


class RealityConfidenceSignalAggregator:
    """Aggregate existing grounding signals without claiming calibrated probability."""

    def aggregate_result(
        self,
        evidence_quality: dict[str, Any],
        linking: dict[str, Any],
        freshness: dict[str, Any],
        conflicts: dict[str, Any],
        *,
        entity: RealityEntity | str | dict[str, Any] | None = None,
    ) -> RealityConfidenceSignalResult:
        for value, name in ((evidence_quality, "evidence_quality"), (linking, "linking"), (freshness, "freshness"), (conflicts, "conflicts")):
            if not isinstance(value, dict):
                raise ValueError(f"{name} must be a dictionary")

        if evidence_quality.get("status") == "not_required":
            return RealityConfidenceSignalResultNormalizer.normalize(
                RealityConfidenceSignalResult(
                    "insufficient", False, None, freshness.get("status", "unavailable"), 0,
                    ("external_evidence_not_required",),
                )
            )
        if evidence_quality.get("status") != "usable":
            return RealityConfidenceSignalResultNormalizer.normalize(
                RealityConfidenceSignalResult(
                    "insufficient", False, 0.0, freshness.get("status", "unavailable"), 0,
                    ("evidence_quality_insufficient",),
                )
            )

        cc = linking.get("claim_count", 0)
        lc = linking.get("linked_claim_count", 0)
        if not isinstance(cc, int) or isinstance(cc, bool) or not isinstance(lc, int) or isinstance(lc, bool) or cc < 0 or lc < 0 or lc > cc:
            raise ValueError("linking claim counts are invalid")
        coverage = None if cc == 0 else lc / cc

        conflicts_count = conflicts.get("conflict_count", 0)
        if not isinstance(conflicts_count, int) or isinstance(conflicts_count, bool) or conflicts_count < 0:
            raise ValueError("conflict_count must be a non-negative integer")
        fs = freshness.get("status")
        if fs not in {"usable", "empty", "unavailable"}:
            raise ValueError("freshness status is invalid")

        signals: list[str] = []
        signals.append("no_extracted_claims" if coverage is None else ("claims_have_evidence_links" if coverage == 1 else "partial_claim_evidence_coverage"))
        linking_unavailable = linking.get("status") == "unavailable"
        if linking_unavailable:
            signals.append("claim_evidence_linking_unavailable")
        stale = 0
        unknown = 0
        if fs == "usable":
            stale = freshness.get("stale_count", 0)
            unknown = freshness.get("unknown_count", 0)
            if not isinstance(stale, int) or isinstance(stale, bool) or stale < 0:
                raise ValueError("stale_count must be a non-negative integer")
            if not isinstance(unknown, int) or isinstance(unknown, bool) or unknown < 0:
                raise ValueError("unknown_count must be a non-negative integer")
            signals.append(
                "stale_sources_present"
                if stale
                else (
                    "freshness_uncertain"
                    if unknown
                    else "sources_within_declared_observation_window"
                )
            )
        else:
            signals.append("freshness_unavailable")

        # Step 219: preserve all legacy direct calls when no entity is
        # supplied. When a caller explicitly supplies an entity, the
        # canonical linked claim text must identify that full entity.
        # This is conservative TEXT alignment, not publisher verification
        # or semantic entailment. Keep the original coverage/freshness/
        # conflict signal values even when support is downgraded.
        named_entity = RealityEntity.validate(entity)
        unaligned_entity = False
        if named_entity.status == "specified":
            unaligned_entity = not explicit_entity_link_alignment(named_entity, linking)
            signals.append(
                "explicit_entity_not_aligned_with_all_linked_claims"
                if unaligned_entity
                else "explicit_entity_text_alignment_only"
            )

        conflicts_unavailable = conflicts.get("status") == "unavailable"
        if conflicts_count:
            signals.append("candidate_conflicts_present")
        if conflicts_unavailable:
            signals.append("conflict_detection_unavailable")
        uncertain = bool(
            coverage is None
            or unaligned_entity
            or linking_unavailable
            or conflicts_unavailable
            or conflicts_count
            or (coverage is not None and coverage < 1)
            or fs != "usable"
            or stale > 0
            or unknown > 0
        )
        return RealityConfidenceSignalResultNormalizer.normalize(
            RealityConfidenceSignalResult(
                "uncertain" if uncertain else "supported",
                True,
                coverage,
                fs,
                conflicts_count,
                tuple(signals),
            )
        )

    def aggregate(self, evidence_quality, linking, freshness, conflicts, *, entity=None):
        return self.aggregate_result(
            evidence_quality, linking, freshness, conflicts, entity=entity
        ).to_dict()


__all__ = ["RealityConfidenceSignalAggregator"]
