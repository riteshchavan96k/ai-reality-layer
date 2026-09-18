from dataclasses import dataclass
from typing import Any

@dataclass(frozen=True)
class RealityState:
    """Canonical immutable snapshot of the evidence-backed reality signals."""
    status: str
    task: str
    evidence: dict[str, Any]
    claims: dict[str, Any]
    claim_evidence_linking: dict[str, Any]
    source_provenance: dict[str, Any]
    source_observation: dict[str, Any]
    freshness: dict[str, Any]
    conflicts: dict[str, Any]
    confidence_signals: dict[str, Any]
    assembly_method: str = "deterministic_signal_snapshot"
    reason: str | None = None
    def __post_init__(self) -> None:
        if self.status not in {"supported", "uncertain", "insufficient", "unavailable"}: raise ValueError("invalid reality state status")
        if not isinstance(self.task,str) or not self.task.strip(): raise ValueError("task must be a non-empty string")
        for value,name in ((self.evidence,"evidence"),(self.claims,"claims"),(self.claim_evidence_linking,"claim_evidence_linking"),(self.source_provenance,"source_provenance"),(self.source_observation,"source_observation"),(self.freshness,"freshness"),(self.conflicts,"conflicts"),(self.confidence_signals,"confidence_signals")):
            if not isinstance(value,dict): raise ValueError(f"{name} must be a dictionary")
        if self.assembly_method != "deterministic_signal_snapshot": raise ValueError("invalid assembly method")
        if self.status == "unavailable" and (not isinstance(self.reason,str) or not self.reason.strip()): raise ValueError("unavailable state requires a reason")
        if self.status != "unavailable" and self.reason is not None: raise ValueError("non-unavailable state cannot contain a reason")
    def to_dict(self) -> dict[str,Any]:
        return {"status":self.status,"task":self.task,"evidence":self.evidence,"claims":self.claims,"claim_evidence_linking":self.claim_evidence_linking,"source_provenance":self.source_provenance,"source_observation":self.source_observation,"freshness":self.freshness,"conflicts":self.conflicts,"confidence_signals":self.confidence_signals,"assembly_method":self.assembly_method,"reason":self.reason}

__all__=["RealityState"]
