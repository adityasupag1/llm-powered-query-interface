from __future__ import annotations

from typing import Any

from pydantic import BaseModel, Field


class QueryRequest(BaseModel):
    question: str = Field(min_length=3, max_length=1000)


class QueryPreviewResponse(BaseModel):
    question: str
    sql: str
    referenced_tables: list[str]
    generation_ms: float


class QueryResponse(QueryPreviewResponse):
    rows: list[dict[str, Any]]
    row_count: int
    execution_ms: float


class ColumnResponse(BaseModel):
    name: str
    data_type: str
    nullable: bool


class TableResponse(BaseModel):
    name: str
    columns: list[ColumnResponse]


class SchemaResponse(BaseModel):
    tables: list[TableResponse]


class HealthResponse(BaseModel):
    status: str
    database: str
    llm_provider: str


class ErrorResponse(BaseModel):
    error: str
    message: str
