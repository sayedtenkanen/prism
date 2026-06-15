"""Updated modules.py with improved error handling for confidence adjustments."""
import json
import logging
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
from app.core.exceptions import InvalidConfidenceAdjustment

logger = logging.getLogger(__name__)

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


def weighted_score(finding: dict[str, Any], agent_name: str) -> float:
    """Calculate weighted confidence score for a finding.

    Args:
        finding: Finding dict with confidence field
        agent_name: Name of the agent providing the finding

    Returns:
        Weighted confidence score
    """
    weight = DOMAIN_WEIGHTS.get(agent_name, 0.5)
    confidence = finding.get("confidence", 0.0)
    try:
        return round(float(confidence) * weight, 3)
    except (ValueError, TypeError) as e:
        logger.warning(f"Invalid confidence value {confidence}: {e}")
        return 0.0


def validate_confidence_adjustment(adjustment: Any, challenger_name: str) -> float:
    """Validate and convert confidence adjustment to float.

    Args:
        adjustment: Raw adjustment value from LLM
        challenger_name: Name of the challenging agent

    Returns:
        Validated adjustment value clamped to [-1.0, 1.0]

    Raises:
        InvalidConfidenceAdjustment: If adjustment cannot be converted to float
    """
    try:
        adj_float = float(adjustment)
    except (ValueError, TypeError) as e:
        logger.error(
            f"Invalid confidence adjustment from {challenger_name}: {adjustment} ({type(adjustment).__name__})"
        )
        raise InvalidConfidenceAdjustment(str(adjustment), challenger_name) from e

    # Clamp to valid range
    if adj_float < -1.0 or adj_float > 1.0:
        logger.warning(
            f"Confidence adjustment {adj_float} from {challenger_name} outside [-1.0, 1.0], clamping"
        )
        return max(-1.0, min(1.0, adj_float))

    return adj_float


class ReviewOrchestrator(dspy.Module):
    """Runs all review agents sequentially and collects findings with error handling."""

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
        """Execute all agents with error handling.

        Args:
            files_changed: List of changed files
            diff: Unified diff of changes

        Returns:
            Dictionary mapping agent names to their results
        """
        results: dict[str, Any] = {}
        for name, agent in self.agents.items():
            try:
                results[name] = agent(files_changed=files_changed, diff=diff)
            except Exception as e:
                logger.error(f"Agent {name} execution failed: {e}", exc_info=True)
                results[name] = {
                    "agent_name": name,
                    "findings": [],
                    "reasoning": f"Agent execution error: {str(e)}",
                    "error": str(e),
                }
        return results


class DebateModule(dspy.Module):
    """Cross-agent debate with comprehensive error handling for confidence adjustments."""

    def __init__(self) -> None:
        super().__init__()
        self.challenge = dspy.ChainOfThought(DebateChallenge)

    def forward(self, agent_results: dict[str, Any], diff: str) -> dict[str, Any]:
        """Execute debate with error handling.

        Args:
            agent_results: Results from all agents
            diff: Unified diff of changes

        Returns:
            Dictionary with debate_records and updated agent_results
        """
        debate_records: list[dict[str, Any]] = []

        for agent_name, challengers in CROSS_CHALLENGES.items():
            source = agent_results.get(agent_name, {})
            findings = source.get("findings", [])
            if not findings:
                continue

            for challenger_name in challengers:
                for finding in findings:
                    confidence = finding.get("confidence", 0.5)
                    if confidence < 0.5:
                        continue

                    try:
                        result = self.challenge(
                            finding=json.dumps(finding),
                            challenger_agent=challenger_name,
                            code_context=diff[:2000],
                        )
                    except Exception as e:
                        logger.error(
                            f"Debate challenge failed: {agent_name} challenged by {challenger_name}: {e}"
                        )
                        continue

                    try:
                        adjustment = validate_confidence_adjustment(result.confidence_adjustment, challenger_name)
                    except InvalidConfidenceAdjustment as e:
                        logger.error(f"Invalid confidence adjustment: {e}")
                        adjustment = 0.0  # No adjustment on error

                    new_confidence = max(0.0, min(1.0, confidence + adjustment))
                    debate_records.append(
                        {
                            "finding": {**finding},
                            "challenged_by": challenger_name,
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
    """Aggregates findings with error handling for parsing."""

    def __init__(self) -> None:
        super().__init__()
        self.judge = dspy.ChainOfThought(JudgeAggregation)

    def forward(self, agent_results: dict[str, Any]) -> dict[str, Any]:
        """Execute judge with error handling.

        Args:
            agent_results: Results from all agents

        Returns:
            Dictionary with aggregated verdict
        """
        all_findings: dict[str, list] = {}
        for agent_name, result in agent_results.items():
            findings = result.get("findings", [])
            all_findings[agent_name] = [{**f, "_weighted_score": weighted_score(f, agent_name)} for f in findings]

        try:
            result = self.judge(all_findings=json.dumps(all_findings))
        except Exception as e:
            logger.error(f"Judge execution failed: {e}", exc_info=True)
            return {
                "summary": "Error during verdict aggregation",
                "critical_findings": [],
                "major_findings": [],
                "minor_findings": [],
                "approved": False,
                "error": str(e),
            }

        return {
            "summary": result.summary,
            "critical_findings": parse_findings(result.critical_findings, agent_name="judge"),
            "major_findings": parse_findings(result.major_findings, agent_name="judge"),
            "minor_findings": parse_findings(result.minor_findings, agent_name="judge"),
            "approved": result.approved,
        }


class FullReviewPipeline(dspy.Module):
    """End-to-end pipeline with comprehensive error handling."""

    def __init__(self) -> None:
        super().__init__()
        self.orchestrator = ReviewOrchestrator()
        self.debate = DebateModule()
        self.judge = JudgeModule()

    def forward(self, files_changed: str, diff: str) -> dict[str, Any]:
        """Execute full pipeline with error handling.

        Args:
            files_changed: List of changed files
            diff: Unified diff of changes

        Returns:
            Dictionary with final verdict and findings
        """
        try:
            agent_results = self.orchestrator(files_changed=files_changed, diff=diff)
            debate_result = self.debate(agent_results=agent_results, diff=diff)
            verdict: dict[str, Any] = self.judge(agent_results=debate_result["agent_results"])
            verdict["debate_records"] = debate_result["debate_records"]
            return verdict
        except Exception as e:
            logger.exception("Full review pipeline failed")
            return {
                "summary": "Review failed due to internal error",
                "critical_findings": [],
                "major_findings": [],
                "minor_findings": [],
                "approved": False,
                "error": str(e),
                "debate_records": [],
            }
