import json
from typing import Any

import dspy

from app.agents.signatures import PerformanceReview


class PerformanceAgent(dspy.Module):
    """Performance review agent — checks for N+1, loops, memory, network, DB issues."""

    def __init__(self) -> None:
        super().__init__()
        self.review = dspy.ChainOfThought(PerformanceReview)

    def forward(self, files_changed: str, diff: str) -> dict[str, Any]:
        result = self.review(files_changed=files_changed, diff=diff)
        try:
            findings = json.loads(result.findings)
        except (json.JSONDecodeError, TypeError):
            findings = []
        return {"agent_name": "performance", "findings": findings, "reasoning": result.rationale}
