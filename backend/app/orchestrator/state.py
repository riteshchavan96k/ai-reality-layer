from dataclasses import dataclass, field
from typing import Any


@dataclass
class OrchestrationState:
    """Mutable state passed across orchestration stages."""

    task: str
    analysis: dict = field(default_factory=dict)
    routing: dict = field(default_factory=dict)
    approval: dict = field(default_factory=dict)
    retrieval: dict = field(default_factory=dict)
    evidence: dict = field(default_factory=dict)
    evidence_quality: dict = field(default_factory=dict)
    grounding: dict = field(default_factory=dict)
    execution: dict = field(default_factory=dict)
    evaluation: dict = field(default_factory=dict)
    recovery: dict = field(default_factory=dict)
    outcome: Any | None = None

    @property
    def retrieval_contract(self) -> dict:
        return self.analysis["reality_retrieval"]

    @property
    def result(self) -> dict | None:
        return self.execution.get("result")
