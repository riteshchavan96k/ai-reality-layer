from dataclasses import dataclass


@dataclass(frozen=True)
class HumanApprovalPolicy:
    """Deterministic prototype policy for deciding when human approval is required."""

    mode: str = "risk_based"
    risk_keywords: tuple[str, ...] = (
        "delete",
        "send",
        "transfer",
        "purchase",
        "publish",
        "deploy",
        "production",
        "medical",
        "legal",
        "financial",
    )

    def evaluate(self, task: str, analysis: dict, routing: dict) -> dict:
        if self.mode not in {"never", "risk_based", "always"}:
            raise ValueError("mode must be one of: never, risk_based, always")

        normalized_task = task.lower()
        matched_keywords = [
            keyword for keyword in self.risk_keywords if keyword in normalized_task
        ]
        ambiguous = analysis.get("confidence", 0.0) < 0.5

        if self.mode == "always":
            required = True
            reason = "Human approval is required by policy."
        elif self.mode == "never":
            required = False
            reason = "Human approval is disabled by policy."
        elif matched_keywords:
            required = True
            reason = "Task matched configured high-risk indicators."
        elif ambiguous:
            required = True
            reason = "Task analysis confidence is below the approval threshold."
        else:
            required = False
            reason = "No configured approval condition was triggered."

        return {
            "required": required,
            "reason": reason,
            "mode": self.mode,
            "risk_level": "high" if matched_keywords else ("ambiguous" if ambiguous else "normal"),
            "matched_keywords": matched_keywords,
        }
