import json
from typing import Any

import dspy

from app.agents.architecture import ArchitectureAgent
from app.agents.base import parse_findings
from app.agents.documentation import DocumentationAgent
from app.agents.maintainability import MaintainabilityAgent
from app.agents.performance import PerformanceAgent
from app.agents.security import SecurityAgent
from app.agents.signatures import DebateChallenge, JudgeAggregation
from app.agents.testing import TestingAgent

DOMAIN_WEIGHTS: dict[str, float] = {
    "security": 1.0,
    "performance": 0.8,
    "maintainability": 0.7,
    "testing": 0.8,
    "architecture": 0.9,
    "documentation": 0.5,
}

CROSS_CHALLENGES: dict[str, list[str]] = {
    "security": ["performance", "architecture"],
    "performance": ["security", "maintainability"],
    "maintainability": ["testing", "architecture"],
    "testing": ["security", "maintainability"],
    "architecture": ["performance", "maintainability"],
    "documentation": ["testing"],
}


def weighted_score(findings: list[dict[str, Any]], agent_name: str) -> float:
    weight = DOMAIN_WEIGHTS.get(agent_name, 0.5)
    if not findings:
        return 0.0
    scores: list[float] = [float(f.get("confidence", 0.0)) * weight for f in findings]
    return round(sum(scores) / len(scores), 3)


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


class DebateModule(dspy.Module):
    """Cross-agent debate — agents challenge findings outside their domain."""

    def __init__(self) -> None:
        super().__init__()
        self.challenge = dspy.ChainOfThought(DebateChallenge)

    def forward(self, agent_results: dict[str, Any], files_changed: str, diff: str) -> dict[str, Any]:
        debate_records: list[dict[str, Any]] = []

        for agent_name, challengers in CROSS_CHALLENGES.items():
            source = agent_results.get(agent_name, {})
            findings = source.get("findings", [])
            if not findings:
                continue

            for challenger_name in challengers:
                for finding in findings:
                    if finding.get("confidence", 0.0) < 0.6:
                        continue
                    result = self.challenge(
                        finding=json.dumps(finding),
                        challenger_agent=challenger_name,
                        code_context=diff[:2000],
                    )
                    adjustment = result.confidence_adjustment
                    new_confidence = max(0.0, min(1.0, finding.get("confidence", 0.5) + adjustment))
                    debate_records.append(
                        {
                            "finding": finding,
                            "challenged_by": agent_name,
                            "challenge_text": result.challenge,
                            "confidence_change": adjustment,
                            "new_confidence": new_confidence,
                            "accepted": new_confidence >= 0.3,
                        }
                    )

                    if new_confidence < 0.3:
                        finding["confidence"] = 0.0
                    else:
                        finding["confidence"] = new_confidence

        return {"debate_records": debate_records, "agent_results": agent_results}


class JudgeModule(dspy.Module):
    """Aggregates findings from all agents into a single deduplicated verdict."""

    def __init__(self) -> None:
        super().__init__()
        self.judge = dspy.ChainOfThought(JudgeAggregation)

    def forward(self, agent_results: dict[str, Any]) -> dict[str, Any]:
        all_findings: dict[str, list] = {}
        for agent_name, result in agent_results.items():
            findings = result.get("findings", [])
            all_findings[agent_name] = [{**f, "_weighted_score": weighted_score([f], agent_name)} for f in findings]

        result = self.judge(all_findings=json.dumps(all_findings))

        return {
            "summary": result.summary,
            "critical_findings": parse_findings(result.critical_findings),
            "major_findings": parse_findings(result.major_findings),
            "minor_findings": parse_findings(result.minor_findings),
            "approved": result.approved,
        }


class FullReviewPipeline(dspy.Module):
    """End-to-end: orchestrator → debate → judge."""

    def __init__(self) -> None:
        super().__init__()
        self.orchestrator = ReviewOrchestrator()
        self.debate = DebateModule()
        self.judge = JudgeModule()

    def forward(self, files_changed: str, diff: str) -> dict[str, Any]:
        agent_results = self.orchestrator(files_changed=files_changed, diff=diff)
        debate_result = self.debate(agent_results=agent_results, files_changed=files_changed, diff=diff)
        verdict: dict[str, Any] = self.judge(agent_results=debate_result["agent_results"])
        verdict["debate_records"] = debate_result["debate_records"]
        return verdict
