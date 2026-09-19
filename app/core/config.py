from __future__ import annotations

from functools import lru_cache

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    app_env: str = "development"
    log_level: str = "INFO"
    database_url: str = "postgresql://query_user:query_password@localhost:5432/query_demo"
    query_timeout_ms: int = Field(default=5000, ge=100, le=60000)
    max_result_rows: int = Field(default=200, ge=1, le=5000)
    llm_provider: str = "mock"
    llm_model: str = "gpt-4.1-mini"
    llm_api_key: str = ""
    llm_base_url: str = "https://api.openai.com/v1"

    model_config = SettingsConfigDict(env_file=".env", extra="ignore")


@lru_cache
def get_settings() -> Settings:
    return Settings()
