import os
from unittest.mock import patch

from app.core.config import DSPyConfig, LLMConfig, SCMConfig, Settings, StorageConfig, TestConfig


class TestLLMConfig:
    def test_defaults(self):
        config = LLMConfig()
        assert config.provider == "openai"
        assert config.judge_model == "gpt-4o"
        assert config.java_reviewer_model == "gpt-4o"
        assert config.python_reviewer_model == "gpt-4o"
        assert config.cpp_reviewer_model == "gpt-4o"
        assert config.ada_reviewer_model == "gpt-4o"
        assert config.docs_reviewer_model == "gpt-4o"
        assert config.temperature == 0.3

    def test_custom_values(self):
        config = LLMConfig(
            provider="ollama",
            judge_model="llama3",
            temperature=0.5,
        )
        assert config.provider == "ollama"
        assert config.judge_model == "llama3"
        assert config.temperature == 0.5

    def test_api_key_from_env(self):
        with patch.dict(os.environ, {"OPENAI_API_KEY": "test-key"}):
            config = LLMConfig()
            assert config.api_key.get_secret_value() == "test-key"

    def test_api_key_default_empty(self):
        with patch.dict(os.environ, {}, clear=True):
            config = LLMConfig()
            assert config.api_key.get_secret_value() == ""


class TestDSPyConfig:
    def test_defaults(self):
        config = DSPyConfig()
        assert config.compiled_prompt_path == "./dspy_prompts"
        assert config.max_bootstrapped_demos == 4
        assert config.max_labeled_demos == 16
        assert config.optimizer == "bootstrapFewShot"
        assert config.optimization_metric == "review_accuracy"
        assert config.use_chain_of_thought is True

    def test_custom_values(self):
        config = DSPyConfig(
            optimizer="mipro",
            max_bootstrapped_demos=8,
            use_chain_of_thought=False,
        )
        assert config.optimizer == "mipro"
        assert config.max_bootstrapped_demos == 8
        assert config.use_chain_of_thought is False


class TestSCMConfig:
    def test_defaults(self):
        config = SCMConfig()
        assert config.provider == "github"
        assert config.github_api_url == "https://api.github.com"
        assert config.bitbucket_url == "https://bitbucket.example.com"

    def test_github_token_from_env(self):
        with patch.dict(os.environ, {"GITHUB_TOKEN": "ghp_test"}):
            config = SCMConfig()
            assert config.github_token.get_secret_value() == "ghp_test"

    def test_bitbucket_token_from_env(self):
        with patch.dict(os.environ, {"BB_TOKEN": "bb-token"}):
            config = SCMConfig()
            assert config.bitbucket_token.get_secret_value() == "bb-token"

    def test_custom_provider(self):
        config = SCMConfig(provider="bitbucket")
        assert config.provider == "bitbucket"


class TestTestConfig:
    def test_defaults(self):
        config = TestConfig()
        assert config.coverage_threshold == 80.0
        assert config.language_thresholds["python"] == 85.0
        assert config.language_thresholds["java"] == 80.0
        assert config.language_thresholds["cpp"] == 75.0
        assert config.language_thresholds["ada"] == 70.0
        assert config.project_thresholds == {}
        assert config.fail_on_coverage_below is True
        assert config.fail_on_test_failure is True
        assert config.timeout == 300

    def test_get_threshold_default(self):
        config = TestConfig()
        assert config.get_threshold("python") == 85.0
        assert config.get_threshold("java") == 80.0
        assert config.get_threshold("unknown") == 80.0

    def test_get_threshold_project_override(self):
        config = TestConfig(project_thresholds={"ENGINEERING": 90.0})
        assert config.get_threshold("python", "ENGINEERING") == 90.0
        assert config.get_threshold("python", "OTHER") == 85.0

    def test_custom_values(self):
        config = TestConfig(
            coverage_threshold=70.0,
            timeout=600,
            fail_on_coverage_below=False,
        )
        assert config.coverage_threshold == 70.0
        assert config.timeout == 600
        assert config.fail_on_coverage_below is False


class TestStorageConfig:
    def test_defaults(self):
        config = StorageConfig()
        assert config.db_path == "prism.db"
        assert config.json_storage_path == "./reports"
        assert config.postgres_url == "postgresql+asyncpg://localhost:5432/prism"

    def test_custom_values(self):
        config = StorageConfig(db_path="/tmp/test.db", json_storage_path="/tmp/reports")
        assert config.db_path == "/tmp/test.db"
        assert config.json_storage_path == "/tmp/reports"


class TestSettings:
    def test_defaults(self):
        settings = Settings()
        assert settings.hitl_enabled is True
        assert settings.retry_max_attempts == 3
        assert settings.log_level == "INFO"
        assert isinstance(settings.llm, LLMConfig)
        assert isinstance(settings.dspy, DSPyConfig)
        assert isinstance(settings.scm, SCMConfig)
        assert isinstance(settings.test, TestConfig)
        assert isinstance(settings.storage, StorageConfig)

    def test_custom_values(self):
        settings = Settings(
            hitl_enabled=False,
            retry_max_attempts=5,
            log_level="DEBUG",
        )
        assert settings.hitl_enabled is False
        assert settings.retry_max_attempts == 5
        assert settings.log_level == "DEBUG"
