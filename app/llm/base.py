from __future__ import annotations

from typing import Protocol


class SQLGenerator(Protocol):
    def generate_sql(self, prompt: str) -> str: ...
