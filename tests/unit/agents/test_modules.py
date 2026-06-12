from unittest.mock import MagicMock

import dspy
import pytest

from app.agents.architecture import ArchitectureAgent
from app.agents.base import BaseAgent, parse_findings
from app.agents.documentation import DocumentationAgent
from app.agents.maintainability import MaintainabilityAgent
from app.agents.modules import JudgeModule, ReviewOrchestrator
from app.agents.performance import PerformanceAgent
from app.agents.security import SecurityAgent
from app.agents.testing import TestingAgent

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


class TestBaseAgent:
    def test_subclass_inherits_forward(self):
        assert issubclass(SecurityAgent, BaseAgent)
        assert issubclass(PerformanceAgent, BaseAgent)
        assert issubclass(MaintainabilityAgent, BaseAgent)
        assert issubclass(TestingAgent, BaseAgent)
        assert issubclass(ArchitectureAgent, BaseAgent)
        assert issubclass(DocumentationAgent, BaseAgent)

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
        [
            SecurityAgent,
            PerformanceAgent,
            MaintainabilityAgent,
            TestingAgent,
            ArchitectureAgent,
            DocumentationAgent,
        ],
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
        assert "security" in orch.agents
        assert "performance" in orch.agents
        assert "maintainability" in orch.agents
        assert "testing" in orch.agents
        assert "architecture" in orch.agents
        assert "documentation" in orch.agents

    def test_forward_calls_all_agents(self):
        orch = ReviewOrchestrator()
        mock_result = {
            "agent_name": "test",
            "findings": [],
            "reasoning": "test",
        }
        for agent in orch.agents.values():
            agent.forward = MagicMock(return_value=mock_result)

        result = orch(files_changed="test.py", diff="+line")
        assert isinstance(result, dict)
        assert len(result) == 6
        for agent_name in orch.agents:
            orch.agents[agent_name].forward.assert_called_once()


class TestJudgeModule:
    def test_init(self):
        judge = JudgeModule()
        assert isinstance(judge, dspy.Module)

    def test_forward_aggregates(self):
        judge = JudgeModule()
        mock_result = MagicMock()
        mock_result.summary = "All clear"
        mock_result.critical_findings = "[]"
        mock_result.major_findings = "[]"
        mock_result.minor_findings = '[{"finding": "minor issue"}]'
        mock_result.approved = True
        judge.judge = MagicMock(return_value=mock_result)

        agent_results = {
            "security": {"findings": []},
            "performance": {"findings": []},
        }
        result = judge(agent_results=agent_results)
        assert isinstance(result, dict)
        assert result["summary"] == "All clear"
        assert result["approved"] is True
        assert isinstance(result["critical_findings"], list)
        assert isinstance(result["major_findings"], list)
        assert isinstance(result["minor_findings"], list)

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
