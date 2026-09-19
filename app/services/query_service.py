from __future__ import annotations

import logging
import time
from dataclasses import dataclass
from typing import Any

from app.db.postgres import PostgresDatabase
from app.llm.base import SQLGenerator
from app.services.prompt_builder import build_sql_prompt
from app.services.sql_validator import SQLSafetyValidator

logger = logging.getLogger(__name__)


@dataclass(frozen=True)
class QueryResult:
    question: str
    sql: str
    rows: list[dict[str, Any]]
    row_count: int
    referenced_tables: tuple[str, ...]
    generation_ms: float
    execution_ms: float


@dataclass(frozen=True)
class QueryPreview:
    question: str
    sql: str
    referenced_tables: tuple[str, ...]
    generation_ms: float


class QueryService:
    def __init__(
        self,
        database: PostgresDatabase,
        generator: SQLGenerator,
        validator: SQLSafetyValidator,
        max_rows: int,
    ):
        self.database = database
        self.generator = generator
        self.validator = validator
        self.max_rows = max_rows

    def preview(self, question: str) -> QueryPreview:
        schema = self.database.introspect_schema()
        prompt = build_sql_prompt(question, schema, self.max_rows)
        generation_started = time.perf_counter()
        generated = self.generator.generate_sql(prompt)
        generation_ms = (time.perf_counter() - generation_started) * 1000
        validated = self.validator.validate(generated, schema)
        logger.info("Validated generated SQL for question=%r", question)
        return QueryPreview(
            question=question,
            sql=validated.sql,
            referenced_tables=validated.referenced_tables,
            generation_ms=round(generation_ms, 2),
        )

    def execute(self, question: str) -> QueryResult:
        preview = self.preview(question)
        execution_started = time.perf_counter()
        rows = self.database.execute_readonly(preview.sql)
        execution_ms = (time.perf_counter() - execution_started) * 1000
        return QueryResult(
            question=question,
            sql=preview.sql,
            rows=rows,
            row_count=len(rows),
            referenced_tables=preview.referenced_tables,
            generation_ms=preview.generation_ms,
            execution_ms=round(execution_ms, 2),
        )
