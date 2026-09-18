from typing import Any
from backend.app.reality.reality_state import RealityState

class RealityStateBuilder:
    """Assemble a deterministic snapshot from already-computed reality signals."""
    def build_result(self, task: str, evidence: dict[str,Any], claims: dict[str,Any], linking: dict[str,Any], provenance: dict[str,Any], observation: dict[str,Any], freshness: dict[str,Any], conflicts: dict[str,Any], confidence: dict[str,Any]) -> RealityState:
        if not isinstance(confidence,dict): raise ValueError("confidence must be a dictionary")
        status=confidence.get("status")
        if status not in {"supported","uncertain","insufficient","unavailable"}: raise ValueError("confidence status is invalid")
        reason=confidence.get("reason")
        return RealityState(status,task,evidence,claims,linking,provenance,observation,freshness,conflicts,confidence,reason=reason)
    def build(self,task,evidence,claims,linking,provenance,observation,freshness,conflicts,confidence):
        return self.build_result(task,evidence,claims,linking,provenance,observation,freshness,conflicts,confidence).to_dict()

__all__=["RealityStateBuilder"]
