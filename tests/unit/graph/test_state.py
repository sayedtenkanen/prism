from app.graph.state import PRReviewState, create_initial_state


class TestPRReviewState:
    def test_state_type_hints(self):
        state = PRReviewState(
            owner="octocat",
            repo="hello-world",
            pr_number=42,
            scm_token="tok",
            hitl_enabled=True,
        )
        assert state["owner"] == "octocat"
        assert state["repo"] == "hello-world"
        assert state["pr_number"] == 42
        assert state["hitl_enabled"] is True

    def test_state_partial_creation(self):
        state = PRReviewState(
            owner="octocat",
            repo="hello-world",
            pr_number=42,
        )
        assert state["owner"] == "octocat"
        assert state.get("diff") is None
        assert state.get("files_changed") is None


class TestCreateInitialState:
    def test_create_initial_state_defaults(self):
        state = create_initial_state(
            owner="octocat",
            repo="hello-world",
            pr_number=42,
            scm_token="tok_123",
        )
        assert state["owner"] == "octocat"
        assert state["repo"] == "hello-world"
        assert state["pr_number"] == 42
        assert state["hitl_enabled"] is True
        assert state["scm_provider"] == "github"
        assert state["llm_model"] == "gpt-4o"
        assert state["pr_metadata"] is None
        assert state["diff"] is None
        assert state["files_changed"] is None
        assert state["languages"] == []
        assert state["debate_records"] == []
        assert state["critical_findings"] == []
        assert state["approved"] is False
        assert state["errors"] == []
        assert state["retry_counts"] == {}

    def test_create_initial_state_custom(self):
        state = create_initial_state(
            owner="octocat",
            repo="hello-world",
            pr_number=42,
            scm_token="tok",
            hitl_enabled=False,
            llm_model="gpt-4o-mini",
            llm_api_key="key",
        )
        assert state["hitl_enabled"] is False
        assert state["llm_model"] == "gpt-4o-mini"
        assert state["llm_api_key"] == "key"

    def test_state_is_mutable(self):
        state = create_initial_state(
            owner="octocat",
            repo="hello-world",
            pr_number=42,
            scm_token="tok",
        )
        state["diff"] = "+new line"
        state["languages"] = ["python"]
        state["errors"].append("test error")
        state["retry_counts"]["fetch_pr"] = 1

        assert state["diff"] == "+new line"
        assert state["languages"] == ["python"]
        assert state["errors"] == ["test error"]
        assert state["retry_counts"]["fetch_pr"] == 1
