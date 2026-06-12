import os
from typing import Optional

from pydantic import Field, SecretStr
from pydantic_settings import BaseSettings


class LLMConfig(BaseSettings):
    """LLM configuration with support for multiple providers."""

    provider: str = "openai"
    judge_model: str = "gpt-4o"
    java_reviewer_model: str = "gpt-4o"
    python_reviewer_model: str = "gpt-4o"
    cpp_reviewer_model: str = "gpt-4o"
    ada_reviewer_model: str = "gpt-4o"
    docs_reviewer_model: str = "gpt-4o"
    temperature: float = 0.3
    api_key: SecretStr = Field(default_factory=lambda: SecretStr(os.environ.get("OPENAI_API_KEY", "")))

    model_config = {"env_prefix": "LLM_"}


class DSPyConfig(BaseSettings):
    """DSPy framework configuration."""

    compiled_prompt_path: str = "./dspy_prompts"
    max_bootstrapped_demos: int = 4
    max_labeled_demos: int = 16
    optimizer: str = "bootstrapFewShot"  # bootstrapFewShot, mipro, copro, gepa
    optimization_metric: str = "review_accuracy"
    use_chain_of_thought: bool = True

    model_config = {"env_prefix": "DSPY_"}


class SCMConfig(BaseSettings):
    """Source Code Management provider configuration."""

    provider: str = "github"  # github or bitbucket
    github_token: SecretStr = Field(default_factory=lambda: SecretStr(os.environ.get("GITHUB_TOKEN", "")))
    github_api_url: str = "https://api.github.com"
    bitbucket_url: str = "https://bitbucket.example.com"
    bitbucket_token: SecretStr = Field(default_factory=lambda: SecretStr(os.environ.get("BB_TOKEN", "")))

    model_config = {"env_prefix": "SCM_"}


class TestConfig(BaseSettings):
    """Test execution configuration."""

    coverage_threshold: float = 80.0
    language_thresholds: dict[str, float] = {
        "python": 85.0,
        "java": 80.0,
        "cpp": 75.0,
        "ada": 70.0,
    }
    project_thresholds: dict[str, float] = {}
    fail_on_coverage_below: bool = True
    fail_on_test_failure: bool = True
    timeout: int = 300

    def get_threshold(self, language: str, project_key: Optional[str] = None) -> float:
        """Get coverage threshold for a language/project combination."""
        if project_key and project_key in self.project_thresholds:
            return self.project_thresholds[project_key]
        return self.language_thresholds.get(language, self.coverage_threshold)


class StorageConfig(BaseSettings):
    """Storage configuration."""

    db_path: str = "prism.db"
    json_storage_path: str = "./reports"
    postgres_url: str = "postgresql+asyncpg://localhost:5432/prism"

    model_config = {"env_prefix": "STORAGE_"}


class Settings(BaseSettings):
    """Main application settings."""

    llm: LLMConfig = LLMConfig()
    dspy: DSPyConfig = DSPyConfig()
    scm: SCMConfig = SCMConfig()
    test: TestConfig = TestConfig()
    storage: StorageConfig = StorageConfig()

    hitl_enabled: bool = True
    retry_max_attempts: int = 3
    log_level: str = "INFO"

    model_config = {"env_prefix": "PRISM_"}


settings = Settings()
