import json
from typing import Any

import dspy

from app.agents.signatures import TestingReview


class TestingAgent(dspy.Module):
    """Testing review agent — checks for coverage gaps, weak assertions, regression risks."""

    def __init__(self) -> None:
        super().__init__()
        self.review = dspy.ChainOfThought(TestingReview)

    def forward(self, files_changed: str, diff: str) -> dict[str, Any]:
        result = self.review(files_changed=files_changed, diff=diff)
        try:
            findings = json.loads(result.findings)
        except (json.JSONDecodeError, TypeError):
            findings = []
        return {"agent_name": "testing", "findings": findings, "reasoning": result.rationale}
