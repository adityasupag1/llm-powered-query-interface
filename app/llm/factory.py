from __future__ import annotations

from app.core.config import Settings
from app.llm.base import SQLGenerator
from app.llm.mock import MockSQLGenerator
from app.llm.openai_compatible import OpenAICompatibleSQLGenerator


def build_sql_generator(settings: Settings) -> SQLGenerator:
    provider = settings.llm_provider.lower()
    if provider == "mock":
        return MockSQLGenerator()
    if provider in {"openai", "openai-compatible"}:
        return OpenAICompatibleSQLGenerator(
            api_key=settings.llm_api_key,
            base_url=settings.llm_base_url,
            model=settings.llm_model,
        )
    raise ValueError(f"Unsupported LLM provider: {settings.llm_provider}")
