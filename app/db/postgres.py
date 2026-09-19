from __future__ import annotations

import logging
from collections.abc import Iterator
from contextlib import contextmanager
from typing import Any

import psycopg
from psycopg.rows import dict_row

from app.core.errors import DatabaseUnavailableError, QueryExecutionError
from app.db.schema import ColumnInfo, DatabaseSchema, TableInfo


logger = logging.getLogger(__name__)


class PostgresDatabase:
    def __init__(self, database_url: str, timeout_ms: int, max_rows: int):
        self.database_url = database_url
        self.timeout_ms = timeout_ms
        self.max_rows = max_rows

    @contextmanager
    def _connect(self) -> Iterator[psycopg.Connection[Any]]:
        try:
            with psycopg.connect(self.database_url, row_factory=dict_row) as connection:
                yield connection
        except psycopg.OperationalError as exc:
            logger.error("PostgreSQL connection failed: %s", exc)
            raise DatabaseUnavailableError("PostgreSQL is unavailable") from exc

    def healthcheck(self) -> bool:
        with self._connect() as connection, connection.cursor() as cursor:
            cursor.execute("SELECT 1")
            return cursor.fetchone() is not None

    def introspect_schema(self) -> DatabaseSchema:
        query = """
            SELECT table_name, column_name, data_type, is_nullable
            FROM information_schema.columns
            WHERE table_schema = 'public'
            ORDER BY table_name, ordinal_position
        """
        by_table: dict[str, list[ColumnInfo]] = {}
        with self._connect() as connection, connection.cursor() as cursor:
            cursor.execute(query)
            for row in cursor.fetchall():
                by_table.setdefault(row["table_name"], []).append(
                    ColumnInfo(
                        name=row["column_name"],
                        data_type=row["data_type"],
                        nullable=row["is_nullable"] == "YES",
                    )
                )
        return DatabaseSchema(
            tables=tuple(
                TableInfo(name=table, columns=tuple(columns))
                for table, columns in sorted(by_table.items())
            )
        )

    def execute_readonly(self, sql: str) -> list[dict[str, Any]]:
        try:
            with self._connect() as connection:
                with connection.transaction():
                    with connection.cursor() as cursor:
                        cursor.execute("SET TRANSACTION READ ONLY")
                        cursor.execute(
                            "SELECT set_config('statement_timeout', %s, true)",
                            (str(self.timeout_ms),),
                        )
                        cursor.execute(sql)
                        rows = cursor.fetchmany(self.max_rows + 1)
                        if len(rows) > self.max_rows:
                            raise QueryExecutionError(
                                f"Query returned more than {self.max_rows} rows"
                            )
                        return [dict(row) for row in rows]
        except QueryExecutionError:
            raise
        except psycopg.errors.QueryCanceled as exc:
            raise QueryExecutionError(
                f"Query exceeded the {self.timeout_ms} ms execution timeout"
            ) from exc
        except psycopg.Error as exc:
            raise QueryExecutionError(
                f"PostgreSQL rejected the query: {exc.diag.message_primary}"
            ) from exc
