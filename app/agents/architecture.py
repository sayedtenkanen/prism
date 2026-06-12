import json
from typing import Any

import dspy

from app.agents.signatures import ArchitectureReview


class ArchitectureAgent(dspy.Module):
    """Architecture review agent — checks for layer violations, coupling, domain consistency."""

    def __init__(self) -> None:
        super().__init__()
        self.review = dspy.ChainOfThought(ArchitectureReview)

    def forward(self, files_changed: str, diff: str) -> dict[str, Any]:
        result = self.review(files_changed=files_changed, diff=diff)
        try:
            findings = json.loads(result.findings)
        except (json.JSONDecodeError, TypeError):
            findings = []
        return {"agent_name": "architecture", "findings": findings, "reasoning": result.rationale}
