from unittest.mock import MagicMock, patch

import dspy
import pytest

from app.agents.architecture import ArchitectureAgent
from app.agents.base import BaseAgent, parse_findings
from app.agents.documentation import DocumentationAgent
from app.agents.maintainability import MaintainabilityAgent
from app.agents.modules import (
    CROSS_CHALLENGES,
    DOMAIN_WEIGHTS,
    DebateModule,
    FullReviewPipeline,
    JudgeModule,
    ReviewOrchestrator,
    weighted_score,
)
from app.agents.performance import PerformanceAgent
from app.agents.security import SecurityAgent
from app.agents.testing import TestingAgent
from app.graph.nodes.review_pipeline import get_pipeline, run_review_pipeline

AGENTS = [
    (SecurityAgent, "security"),
    (PerformanceAgent, "performance"),
    (MaintainabilityAgent, "maintainability"),
    (TestingAgent, "testing"),
    (ArchitectureAgent, "architecture"),
    (DocumentationAgent, "documentation"),
]


class TestParseFindings:
    def test_list_passthrough(self):
        data = [{"finding": "x"}]
        assert parse_findings(data) is data

    def test_json_string(self):
        assert parse_findings('[{"finding": "x"}]') == [{"finding": "x"}]

    def test_invalid_json_string(self):
        assert parse_findings("not json") == []

    def test_none_returns_empty(self):
        assert parse_findings(None) == []

    def test_int_returns_empty(self):
        assert parse_findings(42) == []


class TestWeightedScore:
    def test_zero_confidence(self):
        assert weighted_score({"confidence": 0.0}, "security") == 0.0

    def test_applies_domain_weight(self):
        result = weighted_score({"confidence": 1.0}, "documentation")
        assert result == 0.5

    def test_unknown_agent_uses_default(self):
        result = weighted_score({"confidence": 1.0}, "unknown")
        assert result == 0.5

    def test_missing_confidence_defaults_to_zero(self):
        result = weighted_score({}, "security")
        assert result == 0.0


class TestDomainWeights:
    def test_all_agents_have_weights(self):
        assert len(DOMAIN_WEIGHTS) == 6
        for agent_name in ["security", "performance", "maintainability", "testing", "architecture", "documentation"]:
            assert agent_name in DOMAIN_WEIGHTS

    def test_cross_challenges_cover_all_agents(self):
        assert len(CROSS_CHALLENGES) == 6
        for agent_name in CROSS_CHALLENGES:
            assert isinstance(CROSS_CHALLENGES[agent_name], list)


class TestBaseAgent:
    def test_subclass_inherits_forward(self):
        assert issubclass(SecurityAgent, BaseAgent)

    def test_forward_returns_correct_shape(self):
        agent = SecurityAgent()
        mock_result = MagicMock()
        mock_result.findings = '[{"finding": "test", "severity": "low", "confidence": 0.5}]'
        mock_result.rationale = "Test reasoning"
        agent.review = MagicMock(return_value=mock_result)
        result = agent(files_changed="test.py", diff="+new line")
        assert result == {
            "agent_name": "security",
            "findings": [{"finding": "test", "severity": "low", "confidence": 0.5}],
            "reasoning": "Test reasoning",
        }

    def test_forward_handles_list_findings(self):
        agent = SecurityAgent()
        mock_result = MagicMock()
        mock_result.findings = [{"finding": "already a list"}]
        mock_result.rationale = "reasoning"
        agent.review = MagicMock(return_value=mock_result)
        result = agent(files_changed="x.py", diff="+y")
        assert result["findings"] == [{"finding": "already a list"}]

    def test_forward_handles_invalid_json(self):
        agent = SecurityAgent()
        mock_result = MagicMock()
        mock_result.findings = "not valid json"
        mock_result.rationale = "reasoning"
        agent.review = MagicMock(return_value=mock_result)
        result = agent(files_changed="x.py", diff="+y")
        assert result["findings"] == []


class TestAllAgents:
    @pytest.mark.parametrize("agent_class,agent_name", AGENTS)
    def test_agent_is_dspy_module(self, agent_class, agent_name):
        agent = agent_class()
        assert isinstance(agent, dspy.Module)

    @pytest.mark.parametrize("agent_class,agent_name", AGENTS)
    def test_agent_forward_returns_dict(self, agent_class, agent_name):
        agent = agent_class()
        mock_result = MagicMock()
        mock_result.findings = '[{"finding": "test", "severity": "low", "confidence": 0.5}]'
        mock_result.rationale = "Test reasoning"
        agent.review = MagicMock(return_value=mock_result)
        result = agent(files_changed="test.py", diff="+new line")
        assert isinstance(result, dict)
        assert result["agent_name"] == agent_name
        assert isinstance(result["findings"], list)
        assert isinstance(result["reasoning"], str)

    @pytest.mark.parametrize(
        "agent_class",
        [SecurityAgent, PerformanceAgent, MaintainabilityAgent, TestingAgent, ArchitectureAgent, DocumentationAgent],
    )
    def test_agent_handles_invalid_json(self, agent_class):
        agent = agent_class()
        mock_result = MagicMock()
        mock_result.findings = "not valid json"
        mock_result.rationale = "reasoning"
        agent.review = MagicMock(return_value=mock_result)
        result = agent(files_changed="test.py", diff="+line")
        assert result["findings"] == []


class TestReviewOrchestrator:
    def test_init(self):
        orch = ReviewOrchestrator()
        assert isinstance(orch, dspy.Module)
        assert len(orch.agents) == 6

    def test_forward_calls_all_agents(self):
        orch = ReviewOrchestrator()
        mock_result = {"agent_name": "test", "findings": [], "reasoning": "test"}
        for agent in orch.agents.values():
            agent.forward = MagicMock(return_value=mock_result)

        result = orch(files_changed="test.py", diff="+line")
        assert len(result) == 6
        for agent_name in orch.agents:
            orch.agents[agent_name].forward.assert_called_once()


class TestDebateModule:
    def test_init(self):
        debate = DebateModule()
        assert isinstance(debate, dspy.Module)

    def test_no_findings_skips_challenge(self):
        debate = DebateModule()
        agent_results = {
            "security": {"findings": []},
            "performance": {"findings": []},
        }
        result = debate(agent_results=agent_results, diff="+y")
        assert result["debate_records"] == []

    def test_low_confidence_findings_skipped(self):
        debate = DebateModule()
        agent_results = {
            "security": {"findings": [{"finding": "x", "confidence": 0.2}]},
        }
        result = debate(agent_results=agent_results, diff="+y")
        assert result["debate_records"] == []

    def test_boundary_confidence_exactly_0_6_is_challenged(self):
        debate = DebateModule()
        mock_result = MagicMock()
        mock_result.challenge = "Borderline"
        mock_result.confidence_adjustment = -0.1
        debate.challenge = MagicMock(return_value=mock_result)

        agent_results = {
            "security": {"findings": [{"finding": "x", "confidence": 0.6}]},
        }
        result = debate(agent_results=agent_results, diff="+y")
        assert len(result["debate_records"]) == len(CROSS_CHALLENGES["security"])

    def test_confidence_0_49_not_challenged(self):
        debate = DebateModule()
        agent_results = {
            "security": {"findings": [{"finding": "x", "confidence": 0.49}]},
        }
        result = debate(agent_results=agent_results, diff="+y")
        assert result["debate_records"] == []

    def test_challenge_reduces_confidence(self):
        debate = DebateModule()
        mock_result = MagicMock()
        mock_result.challenge = "Invalid finding"
        mock_result.confidence_adjustment = -0.5
        debate.challenge = MagicMock(return_value=mock_result)

        agent_results = {
            "security": {"findings": [{"finding": "x", "confidence": 0.8}]},
        }
        result = debate(agent_results=agent_results, diff="+y")
        assert len(result["debate_records"]) == 1
        assert result["debate_records"][0]["new_confidence"] == pytest.approx(0.3)

    def test_challenge_clamps_to_zero(self):
        debate = DebateModule()
        mock_result = MagicMock()
        mock_result.challenge = "Overconfident"
        mock_result.confidence_adjustment = -2.0
        debate.challenge = MagicMock(return_value=mock_result)

        agent_results = {
            "security": {"findings": [{"finding": "x", "confidence": 0.8}]},
        }
        result = debate(agent_results=agent_results, diff="+y")
        assert result["debate_records"][0]["new_confidence"] == 0.0

    def test_challenge_clamps_to_one(self):
        debate = DebateModule()
        mock_result = MagicMock()
        mock_result.challenge = "Confirmed"
        mock_result.confidence_adjustment = 0.5
        debate.challenge = MagicMock(return_value=mock_result)

        agent_results = {
            "security": {"findings": [{"finding": "x", "confidence": 0.8}]},
        }
        result = debate(agent_results=agent_results, diff="+y")
        assert result["debate_records"][0]["new_confidence"] == 1.0

    def test_missing_confidence_defaults_to_0_5(self):
        debate = DebateModule()
        mock_result = MagicMock()
        mock_result.challenge = "Adjusted"
        mock_result.confidence_adjustment = -0.2
        debate.challenge = MagicMock(return_value=mock_result)

        agent_results = {
            "security": {"findings": [{"finding": "x"}]},
        }
        result = debate(agent_results=agent_results, diff="+y")
        assert len(result["debate_records"]) == 1
        assert result["debate_records"][0]["new_confidence"] == pytest.approx(0.3)

    def test_accepted_when_above_threshold(self):
        debate = DebateModule()
        mock_result = MagicMock()
        mock_result.challenge = "Minor issue"
        mock_result.confidence_adjustment = -0.1
        debate.challenge = MagicMock(return_value=mock_result)

        agent_results = {
            "security": {"findings": [{"finding": "x", "confidence": 0.8}]},
        }
        result = debate(agent_results=agent_results, diff="+y")
        assert result["debate_records"][0]["accepted"] is True

    def test_challenged_by_is_challenger_not_source(self):
        debate = DebateModule()
        mock_result = MagicMock()
        mock_result.challenge = "Challenge"
        mock_result.confidence_adjustment = -0.1
        debate.challenge = MagicMock(return_value=mock_result)

        agent_results = {
            "security": {"findings": [{"finding": "x", "confidence": 0.8}]},
        }
        result = debate(agent_results=agent_results, diff="+y")
        record = result["debate_records"][0]
        assert record["challenged_by"] == "performance" or record["challenged_by"] == "architecture"
        assert record["challenged_by"] != "security"

    def test_finding_is_shallow_copy_not_mutation(self):
        debate = DebateModule()
        mock_result = MagicMock()
        mock_result.challenge = "Adjust"
        mock_result.confidence_adjustment = -0.5
        debate.challenge = MagicMock(return_value=mock_result)

        original_finding = {"finding": "x", "confidence": 0.8}
        agent_results = {
            "security": {"findings": [original_finding]},
        }
        result = debate(agent_results=agent_results, diff="+y")
        assert result["debate_records"][0]["finding"]["confidence"] == 0.8
        assert original_finding["confidence"] == pytest.approx(0.3)


class TestJudgeModule:
    def test_init(self):
        judge = JudgeModule()
        assert isinstance(judge, dspy.Module)

    def test_forward_aggregates_with_weighted_scores(self):
        judge = JudgeModule()
        mock_result = MagicMock()
        mock_result.summary = "All clear"
        mock_result.critical_findings = "[]"
        mock_result.major_findings = "[]"
        mock_result.minor_findings = '[{"finding": "minor issue"}]'
        mock_result.approved = True
        judge.judge = MagicMock(return_value=mock_result)

        agent_results = {
            "security": {"findings": [{"finding": "x", "confidence": 0.8}]},
            "performance": {"findings": []},
        }
        result = judge(agent_results=agent_results)
        assert result["summary"] == "All clear"
        assert result["approved"] is True

        call_args = judge.judge.call_args
        all_findings = call_args.kwargs.get("all_findings", call_args[1].get("all_findings", ""))
        assert "_weighted_score" in all_findings

    def test_forward_handles_list_inputs(self):
        judge = JudgeModule()
        mock_result = MagicMock()
        mock_result.summary = "Test"
        mock_result.critical_findings = [{"finding": "crit"}]
        mock_result.major_findings = []
        mock_result.minor_findings = []
        mock_result.approved = False
        judge.judge = MagicMock(return_value=mock_result)

        result = judge(agent_results={"security": {"findings": []}})
        assert result["approved"] is False
        assert len(result["critical_findings"]) == 1


class TestFullReviewPipeline:
    def test_init(self):
        pipe = FullReviewPipeline()
        assert isinstance(pipe, dspy.Module)
        assert hasattr(pipe, "orchestrator")
        assert hasattr(pipe, "judge")

    def test_forward_returns_verdict(self):
        pipe = FullReviewPipeline()
        pipe.orchestrator = MagicMock(
            return_value={
                "security": {"findings": []},
                "performance": {"findings": []},
            }
        )
        pipe.debate = MagicMock(
            return_value={
                "debate_records": [],
                "agent_results": {
                    "security": {"findings": []},
                    "performance": {"findings": []},
                },
            }
        )
        pipe.judge = MagicMock(
            return_value={
                "summary": "OK",
                "critical_findings": [],
                "major_findings": [],
                "minor_findings": [],
                "approved": True,
            }
        )

        result = pipe(files_changed="x.py", diff="+y")
        assert result["summary"] == "OK"
        assert result["approved"] is True
        assert "debate_records" in result


class TestReviewPipelineNode:
    def test_get_pipeline_singleton(self):
        p1 = get_pipeline()
        p2 = get_pipeline()
        assert p1 is p2

    def test_run_review_pipeline(self):
        state = {"files_changed": "x.py", "diff": "+line"}
        mock_verdict = {
            "summary": "OK",
            "critical_findings": [],
            "major_findings": [],
            "minor_findings": [],
            "approved": True,
            "debate_records": [],
        }
        with patch("app.graph.nodes.review_pipeline.get_pipeline") as mock_get:
            mock_pipeline = MagicMock(return_value=mock_verdict)
            mock_get.return_value = mock_pipeline
            import asyncio

            result = asyncio.run(run_review_pipeline(state))
            assert result["approved"] is True
            assert result["review_summary"] == "OK"
