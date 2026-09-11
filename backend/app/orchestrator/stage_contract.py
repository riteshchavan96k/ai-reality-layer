from dataclasses import dataclass
from typing import Any

from backend.app.execution.execution_budget import ExecutionBudget
from backend.app.orchestrator.state import OrchestrationState


@dataclass
class OrchestrationStageContext:
    """Explicit context shared by every orchestration pipeline stage."""

    state: OrchestrationState
    trace: Any
    execution_budget: ExecutionBudget | None = None

    def set_budget(self, budget: ExecutionBudget) -> None:
        self.execution_budget = budget

    def require_budget(self) -> ExecutionBudget:
        if self.execution_budget is None:
            raise RuntimeError("execution budget is not available")
        return self.execution_budget
