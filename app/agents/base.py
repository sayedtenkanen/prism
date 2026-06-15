"""Updated agents/base.py with improved error handling."""
import logging
from typing import Any

import dspy

from app.core.exceptions import ParseFindingsError
from app.core.parsing import parse_findings

logger = logging.getLogger(__name__)


class BaseAgent(dspy.Module):
    """Shared forward logic for all review agents with error handling."""

    agent_name: str
    review: dspy.ChainOfThought

    def forward(self, files_changed: str, diff: str) -> dict[str, Any]:
        """Execute review with comprehensive error handling.

        Args:
            files_changed: List of changed files
            diff: Unified diff of changes

        Returns:
            Dictionary with agent_name, findings (list), and reasoning (str)
        """
        try:
            result = self.review(files_changed=files_changed, diff=diff)
        except Exception as e:
            logger.exception(f"Review execution failed for agent {self.agent_name}")
            return {
                "agent_name": self.agent_name,
                "findings": [],
                "reasoning": f"Error during review: {str(e)}",
                "error": str(e),
            }

        try:
            findings = parse_findings(result.findings, agent_name=self.agent_name)
        except ParseFindingsError as e:
            logger.error(
                f"Failed to parse findings from {self.agent_name}: {e}",
                extra={"raw_findings": e.raw_value[:200]},
            )
            findings = []

        return {
            "agent_name": self.agent_name,
            "findings": findings,
            "reasoning": result.rationale,
        }
