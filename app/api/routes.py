from __future__ import annotations

from fastapi import APIRouter, Request

from app.api.models import (
    ColumnResponse,
    HealthResponse,
    QueryPreviewResponse,
    QueryRequest,
    QueryResponse,
    SchemaResponse,
    TableResponse,
)

router = APIRouter()


@router.get("/health", response_model=HealthResponse)
def health(request: Request) -> HealthResponse:
    services = request.app.state.services
    database_ok = services.database.healthcheck()
    return HealthResponse(
        status="ok" if database_ok else "degraded",
        database="ok" if database_ok else "unavailable",
        llm_provider=services.settings.llm_provider,
    )


@router.get("/schema", response_model=SchemaResponse)
def schema(request: Request) -> SchemaResponse:
    db_schema = request.app.state.services.database.introspect_schema()
    return SchemaResponse(
        tables=[
            TableResponse(
                name=table.name,
                columns=[
                    ColumnResponse(
                        name=column.name,
                        data_type=column.data_type,
                        nullable=column.nullable,
                    )
                    for column in table.columns
                ],
            )
            for table in db_schema.tables
        ]
    )


@router.post("/query/preview", response_model=QueryPreviewResponse)
def preview_query(payload: QueryRequest, request: Request) -> QueryPreviewResponse:
    result = request.app.state.services.query_service.preview(payload.question)
    return QueryPreviewResponse(
        question=result.question,
        sql=result.sql,
        referenced_tables=list(result.referenced_tables),
        generation_ms=result.generation_ms,
    )


@router.post("/query", response_model=QueryResponse)
def execute_query(payload: QueryRequest, request: Request) -> QueryResponse:
    result = request.app.state.services.query_service.execute(payload.question)
    return QueryResponse(
        question=result.question,
        sql=result.sql,
        referenced_tables=list(result.referenced_tables),
        generation_ms=result.generation_ms,
        rows=result.rows,
        row_count=result.row_count,
        execution_ms=result.execution_ms,
    )
