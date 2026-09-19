from __future__ import annotations

from dataclasses import dataclass

from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse

from app.api.routes import router
from app.core.config import Settings, get_settings
from app.core.errors import AppError
from app.core.logging import configure_logging
from app.db.postgres import PostgresDatabase
from app.llm.factory import build_sql_generator
from app.services.query_service import QueryService
from app.services.sql_validator import SQLSafetyValidator


@dataclass
class Services:
    settings: Settings
    database: PostgresDatabase
    query_service: QueryService


def create_app(settings: Settings | None = None) -> FastAPI:
    settings = settings or get_settings()
    configure_logging(settings.log_level)

    database = PostgresDatabase(
        database_url=settings.database_url,
        timeout_ms=settings.query_timeout_ms,
        max_rows=settings.max_result_rows,
    )
    generator = build_sql_generator(settings)
    validator = SQLSafetyValidator(max_rows=settings.max_result_rows)
    query_service = QueryService(
        database=database,
        generator=generator,
        validator=validator,
        max_rows=settings.max_result_rows,
    )

    app = FastAPI(
        title="LLM-Powered Query Interface",
        version="0.1.0",
        description=(
            "Schema-aware natural-language to PostgreSQL interface with read-only SQL validation."
        ),
    )
    app.state.services = Services(
        settings=settings,
        database=database,
        query_service=query_service,
    )
    app.include_router(router)

    @app.exception_handler(AppError)
    async def handle_app_error(_request: Request, exc: AppError) -> JSONResponse:
        return JSONResponse(
            status_code=exc.status_code,
            content={"error": exc.code, "message": exc.message},
        )

    return app


app = create_app()
