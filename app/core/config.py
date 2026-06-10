from typing import List

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", case_sensitive=True)

    PROJECT_NAME: str = "PR Inspection Synthesis"
    API_V1_STR: str = "/api/v1"
    CORS_ORIGINS: List[str] = ["http://localhost:3000", "http://localhost:8000"]

    # Database (future)
    # DATABASE_URL: str = "postgresql://user:password@localhost:5432/db"

    # Auth (future)
    # SECRET_KEY: str = "your-secret-key"
    # ACCESS_TOKEN_EXPIRE_MINUTES: int = 30


settings = Settings()
