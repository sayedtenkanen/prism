from app.core.models import Language
from app.graph.state import PRReviewState, create_initial_state


class TestPRReviewState:
    def test_state_type_hints(self):
        """Verify PRReviewState is a valid TypedDict."""
        state = PRReviewState(
            project_key="TEST",
            repo_slug="repo",
            pr_id="123",
            hitl_enabled=True,
            bb_url="https://bitbucket.example.com",
            bb_token="token",
            llm_provider="openai",
            llm_model="gpt-4o",
            llm_api_key="key",
            llm_temperature=0.3,
            pr_metadata=None,
            diff=None,
            files=[],
            languages=[],
            review_results={},
            test_results=None,
            doc_code_alignment=None,
            previous_review=None,
            comparison=None,
            summary=None,
            verdict=None,
            bb_comment_url=None,
            json_report_path=None,
            review_summary=None,
            errors=[],
            retry_counts={},
        )
        assert state["project_key"] == "TEST"
        assert state["repo_slug"] == "repo"
        assert state["pr_id"] == "123"
        assert state["hitl_enabled"] is True

    def test_state_partial_creation(self):
        """Verify state can be created with minimal fields."""
        state = PRReviewState(
            project_key="TEST",
            repo_slug="repo",
            pr_id="123",
        )
        assert state["project_key"] == "TEST"
        assert state.get("diff") is None
        assert state.get("files") is None


class TestCreateInitialState:
    def test_create_initial_state_defaults(self):
        state = create_initial_state(
            project_key="TEST",
            repo_slug="repo",
            pr_id="123",
            bb_url="https://bitbucket.example.com",
            bb_token="token",
            llm_api_key="key",
        )
        assert state["project_key"] == "TEST"
        assert state["repo_slug"] == "repo"
        assert state["pr_id"] == "123"
        assert state["hitl_enabled"] is True
        assert state["bb_url"] == "https://bitbucket.example.com"
        assert state["bb_token"] == "token"
        assert state["llm_provider"] == "openai"
        assert state["llm_model"] == "gpt-4o"
        assert state["llm_temperature"] == 0.3
        assert state["llm_api_key"] == "key"
        assert state["pr_metadata"] is None
        assert state["diff"] is None
        assert state["files"] == []
        assert state["languages"] == []
        assert state["review_results"] == {}
        assert state["test_results"] is None
        assert state["doc_code_alignment"] is None
        assert state["previous_review"] is None
        assert state["comparison"] is None
        assert state["summary"] is None
        assert state["verdict"] is None
        assert state["bb_comment_url"] is None
        assert state["json_report_path"] is None
        assert state["review_summary"] is None
        assert state["errors"] == []
        assert state["retry_counts"] == {}

    def test_create_initial_state_custom(self):
        state = create_initial_state(
            project_key="ENG",
            repo_slug="api",
            pr_id="456",
            bb_url="https://bb.internal.com",
            bb_token="mytoken",
            llm_api_key="mykey",
            hitl_enabled=False,
            llm_provider="ollama",
            llm_model="llama3",
            llm_temperature=0.5,
        )
        assert state["project_key"] == "ENG"
        assert state["repo_slug"] == "api"
        assert state["pr_id"] == "456"
        assert state["hitl_enabled"] is False
        assert state["llm_provider"] == "ollama"
        assert state["llm_model"] == "llama3"
        assert state["llm_temperature"] == 0.5

    def test_state_is_mutable(self):
        state = create_initial_state(
            project_key="TEST",
            repo_slug="repo",
            pr_id="123",
            bb_url="https://bitbucket.example.com",
            bb_token="token",
            llm_api_key="key",
        )
        state["diff"] = "+new line"
        state["languages"] = [Language.PYTHON]
        state["errors"].append("test error")
        state["retry_counts"]["fetch_pr"] = 1

        assert state["diff"] == "+new line"
        assert state["languages"] == [Language.PYTHON]
        assert state["errors"] == ["test error"]
        assert state["retry_counts"]["fetch_pr"] == 1
