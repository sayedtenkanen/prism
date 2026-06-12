import json
from typing import Any

import dspy

from app.agents.architecture import ArchitectureAgent
from app.agents.base import parse_findings
from app.agents.documentation import DocumentationAgent
from app.agents.maintainability import MaintainabilityAgent
from app.agents.performance import PerformanceAgent
from app.agents.security import SecurityAgent
from app.agents.signatures import JudgeAggregation
from app.agents.testing import TestingAgent


class ReviewOrchestrator(dspy.Module):
    """Runs all review agents sequentially and collects findings."""

    def __init__(self) -> None:
        super().__init__()
        self.agents: dict[str, dspy.Module] = {
            "security": SecurityAgent(),
            "performance": PerformanceAgent(),
            "maintainability": MaintainabilityAgent(),
            "testing": TestingAgent(),
            "architecture": ArchitectureAgent(),
            "documentation": DocumentationAgent(),
        }

    def forward(self, files_changed: str, diff: str) -> dict[str, Any]:
        results: dict[str, Any] = {}
        for name, agent in self.agents.items():
            results[name] = agent(files_changed=files_changed, diff=diff)
        return results


class JudgeModule(dspy.Module):
    """Aggregates findings from all agents into a single deduplicated verdict."""

    def __init__(self) -> None:
        super().__init__()
        self.judge = dspy.ChainOfThought(JudgeAggregation)

    def forward(self, agent_results: dict[str, Any]) -> dict[str, Any]:
        all_findings: dict[str, list] = {}
        for agent_name, result in agent_results.items():
            all_findings[agent_name] = result.get("findings", [])

        result = self.judge(all_findings=json.dumps(all_findings))

        return {
            "summary": result.summary,
            "critical_findings": parse_findings(result.critical_findings),
            "major_findings": parse_findings(result.major_findings),
            "minor_findings": parse_findings(result.minor_findings),
            "approved": result.approved,
        }
