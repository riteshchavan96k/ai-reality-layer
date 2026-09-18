from typing import Any
from backend.app.reality.confidence_signals import RealityConfidenceSignalResult

class RealityConfidenceSignalAggregator:
    """Aggregate existing grounding signals without claiming calibrated probability."""
    def aggregate_result(self, evidence_quality: dict[str, Any], linking: dict[str, Any], freshness: dict[str, Any], conflicts: dict[str, Any]) -> RealityConfidenceSignalResult:
        for value, name in ((evidence_quality,"evidence_quality"),(linking,"linking"),(freshness,"freshness"),(conflicts,"conflicts")):
            if not isinstance(value, dict): raise ValueError(f"{name} must be a dictionary")
        if evidence_quality.get("status") == "not_required": return RealityConfidenceSignalResult("insufficient", False, None, freshness.get("status","unavailable"), 0, ("external_evidence_not_required",))
        if evidence_quality.get("status") != "usable": return RealityConfidenceSignalResult("insufficient", False, 0.0, freshness.get("status","unavailable"), 0, ("evidence_quality_insufficient",))
        cc=linking.get("claim_count",0); lc=linking.get("linked_claim_count",0)
        if not isinstance(cc,int) or not isinstance(lc,int) or cc<0 or lc<0 or lc>cc: raise ValueError("linking claim counts are invalid")
        coverage=None if cc==0 else lc/cc
        conflicts_count=conflicts.get("conflict_count",0)
        if not isinstance(conflicts_count,int) or conflicts_count<0: raise ValueError("conflict_count must be a non-negative integer")
        fs=freshness.get("status")
        if fs not in {"usable","empty","unavailable"}: raise ValueError("freshness status is invalid")
        signals=[]
        signals.append("no_extracted_claims" if coverage is None else ("claims_have_evidence_links" if coverage==1 else "partial_claim_evidence_coverage"))
        linking_unavailable = linking.get("status") == "unavailable"
        if linking_unavailable: signals.append("claim_evidence_linking_unavailable")
        if fs=="usable":
            stale=freshness.get("stale_count",0); unknown=freshness.get("unknown_count",0)
            signals.append("stale_sources_present" if stale else ("freshness_uncertain" if unknown else "sources_within_declared_observation_window"))
        else: signals.append("freshness_unavailable")
        conflicts_unavailable = conflicts.get("status") == "unavailable"
        if conflicts_count: signals.append("candidate_conflicts_present")
        if conflicts_unavailable: signals.append("conflict_detection_unavailable")
        uncertain=bool(coverage is None or linking_unavailable or conflicts_unavailable or conflicts_count or (coverage is not None and coverage<1) or fs!="usable" or freshness.get("stale_count",0)>0)
        return RealityConfidenceSignalResult("uncertain" if uncertain else "supported",True,coverage,fs,conflicts_count,tuple(signals))
    def aggregate(self,evidence_quality,linking,freshness,conflicts): return self.aggregate_result(evidence_quality,linking,freshness,conflicts).to_dict()

__all__=["RealityConfidenceSignalAggregator"]
