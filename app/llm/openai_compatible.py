from __future__ import annotations

import httpx

from app.core.errors import LLMProviderError


class OpenAICompatibleSQLGenerator:
    def __init__(self, api_key: str, base_url: str, model: str, timeout_seconds: float = 30.0):
        self.api_key = api_key
        self.base_url = base_url.rstrip("/")
        self.model = model
        self.timeout_seconds = timeout_seconds

    def generate_sql(self, prompt: str) -> str:
        if not self.api_key:
            raise LLMProviderError("LLM_API_KEY is required for the openai-compatible provider")

        try:
            response = httpx.post(
                f"{self.base_url}/chat/completions",
                headers={"Authorization": f"Bearer {self.api_key}"},
                json={
                    "model": self.model,
                    "temperature": 0,
                    "messages": [
                        {
                            "role": "system",
                            "content": "Return only one PostgreSQL SELECT query. No markdown or explanation.",
                        },
                        {"role": "user", "content": prompt},
                    ],
                },
                timeout=self.timeout_seconds,
            )
            response.raise_for_status()
            payload = response.json()
            content = payload["choices"][0]["message"]["content"].strip()
            if content.startswith("```"):
                content = content.strip("`")
                content = content.removeprefix("sql").strip()
            return content
        except (httpx.HTTPError, KeyError, IndexError, TypeError, ValueError) as exc:
            raise LLMProviderError("LLM provider returned an invalid response") from exc
