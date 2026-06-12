import json
from typing import Any

import dspy

from app.agents.signatures import MaintainabilityReview


class MaintainabilityAgent(dspy.Module):
    """Maintainability review agent — checks for complexity, readability, design smells."""

    def __init__(self) -> None:
        super().__init__()
        self.review = dspy.ChainOfThought(MaintainabilityReview)

    def forward(self, files_changed: str, diff: str) -> dict[str, Any]:
        result = self.review(files_changed=files_changed, diff=diff)
        try:
            findings = json.loads(result.findings)
        except (json.JSONDecodeError, TypeError):
            findings = []
        return {"agent_name": "maintainability", "findings": findings, "reasoning": result.rationale}
