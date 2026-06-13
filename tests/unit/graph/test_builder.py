from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from app.graph.builder import build_graph, get_graph, should_continue
from app.graph.nodes.detect_node import detect_node
from app.graph.nodes.fetch_pr import fetch_pr
from app.graph.nodes.output_node import output_node
from app.graph.nodes.review_node import get_pipeline, review_node
from app.graph.state import create_initial_state


class TestPRReviewState:
    def test_create_initial_state(self):
        state = create_initial_state(
            owner="octocat",
            repo="hello-world",
            pr_number=42,
            scm_token="tok_123",
        )
        assert state["owner"] == "octocat"
        assert state["repo"] == "hello-world"
        assert state["pr_number"] == 42
        assert state["scm_token"] == "tok_123"
        assert state["scm_provider"] == "github"
        assert state["hitl_enabled"] is True
        assert state["errors"] == []
        assert state["debate_records"] == []
        assert state["critical_findings"] == []
        assert state["approved"] is False

    def test_create_initial_state_custom(self):
        state = create_initial_state(
            owner="o",
            repo="r",
            pr_number=1,
            scm_token="t",
            scm_provider="github",
            hitl_enabled=False,
            llm_model="gpt-4o-mini",
            llm_api_key="key",
        )
        assert state["hitl_enabled"] is False
        assert state["llm_model"] == "gpt-4o-mini"
        assert state["llm_api_key"] == "key"


class TestFetchPr:
    @pytest.mark.asyncio
    async def test_fetch_pr_success(self):
        mock_client = AsyncMock()
        mock_client.get_pr = AsyncMock(return_value={"title": "Test PR"})
        mock_client.get_diff = AsyncMock(return_value="diff --git a/file.py")
        mock_client.get_files = AsyncMock(
            return_value=[{"filename": "file.py", "language": "Python", "additions": 10, "deletions": 5}]
        )
        mock_client.close = AsyncMock()

        with patch("app.graph.nodes.fetch_pr.GitHubClient", return_value=mock_client):
            state = {
                "scm_token": "tok",
                "scm_provider": "github",
                "owner": "o",
                "repo": "r",
                "pr_number": 1,
                "errors": [],
            }
            result = await fetch_pr(state)
            assert result["pr_metadata"] == {"title": "Test PR"}
            assert result["diff"] == "diff --git a/file.py"
            assert "file.py" in result["files_changed"]

    @pytest.mark.asyncio
    async def test_fetch_pr_error_clears_stale_data(self):
        mock_client = AsyncMock()
        mock_client.get_pr = AsyncMock(side_effect=Exception("API error"))
        mock_client.close = AsyncMock()

        with patch("app.graph.nodes.fetch_pr.GitHubClient", return_value=mock_client):
            state = {
                "scm_token": "tok",
                "scm_provider": "github",
                "owner": "o",
                "repo": "r",
                "pr_number": 1,
                "errors": [],
                "pr_metadata": {"stale": True},
                "diff": "stale diff",
                "files_changed": "stale files",
            }
            result = await fetch_pr(state)
            assert len(result["errors"]) == 1
            assert result["pr_metadata"] is None
            assert result["diff"] is None
            assert result["files_changed"] is None

    @pytest.mark.asyncio
    async def test_fetch_pr_rejects_non_github(self):
        state = {"scm_token": "tok", "scm_provider": "gitlab", "owner": "o", "repo": "r", "pr_number": 1, "errors": []}
        with pytest.raises(AssertionError, match="Unsupported provider"):
            await fetch_pr(state)


class TestDetectNode:
    @pytest.mark.asyncio
    async def test_detect_node(self):
        state = {"files_changed": "app/main.py (+10/-5)", "diff": "+import os"}
        result = await detect_node(state)
        assert "languages" in result
        assert isinstance(result["languages"], list)


class TestReviewNode:
    @pytest.mark.asyncio
    async def test_review_node(self):
        mock_pipeline = MagicMock(
            return_value={
                "summary": "Looks good",
                "critical_findings": [],
                "major_findings": [],
                "minor_findings": [{"finding": "minor"}],
                "approved": True,
                "debate_records": [],
                "agent_results": {},
            }
        )

        with patch("app.graph.nodes.review_node.get_pipeline", return_value=mock_pipeline):
            state = {"files_changed": "x.py", "diff": "+line", "errors": []}
            result = await review_node(state)
            assert result["summary"] == "Looks good"
            assert result["approved"] is True
            assert len(result["minor_findings"]) == 1

    def test_get_pipeline_singleton(self):
        p1 = get_pipeline()
        p2 = get_pipeline()
        assert p1 is p2


class TestOutputNode:
    @pytest.mark.asyncio
    async def test_output_node(self, tmp_path):
        state = {
            "summary": "OK",
            "approved": True,
            "critical_findings": [],
            "major_findings": [],
            "minor_findings": [],
            "debate_records": [],
            "languages": ["python"],
            "pr_metadata": {"title": "Test"},
            "pr_number": 99,
        }
        with patch("builtins.open", MagicMock()):
            result = await output_node(state)
            assert "json_report_path" in result


class TestShouldContinue:
    def test_errors_goes_to_output(self):
        state = {"errors": ["something broke"]}
        assert should_continue(state) == "output"

    def test_hitl_enabled_goes_to_approval(self):
        state = {"hitl_enabled": True, "errors": []}
        assert should_continue(state) == "human_approval"

    def test_hitl_disabled_goes_to_output(self):
        state = {"hitl_enabled": False, "errors": []}
        assert should_continue(state) == "output"


class TestGraphBuilder:
    def test_build_graph(self):
        graph = build_graph()
        assert graph is not None

    def test_get_graph_singleton(self):
        g1 = get_graph()
        g2 = get_graph()
        assert g1 is g2
