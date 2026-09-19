from __future__ import annotations


class AppError(Exception):
    code = "app_error"
    status_code = 400

    def __init__(self, message: str):
        super().__init__(message)
        self.message = message


class DatabaseUnavailableError(AppError):
    code = "database_unavailable"
    status_code = 503


class LLMProviderError(AppError):
    code = "llm_provider_error"
    status_code = 502


class SQLValidationError(AppError):
    code = "sql_validation_error"
    status_code = 422


class QueryExecutionError(AppError):
    code = "query_execution_error"
    status_code = 422
