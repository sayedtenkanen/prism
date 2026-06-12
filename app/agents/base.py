import json
from typing import Any

import dspy


def parse_findings(raw: Any) -> list[Any]:
    if isinstance(raw, list):
        return raw
    if isinstance(raw, str):
        try:
            return list(json.loads(raw))
        except (json.JSONDecodeError, TypeError):
            return []
    return []


class BaseAgent(dspy.Module):
    """Shared forward logic for all review agents."""

    agent_name: str
    review: dspy.ChainOfThought

    def forward(self, files_changed: str, diff: str) -> dict[str, Any]:
        result = self.review(files_changed=files_changed, diff=diff)
        return {
            "agent_name": self.agent_name,
            "findings": parse_findings(result.findings),
            "reasoning": result.rationale,
        }
