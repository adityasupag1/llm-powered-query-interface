from __future__ import annotations

import os
from pathlib import Path

import psycopg
import pytest
from fastapi.testclient import TestClient

from app.core.config import Settings
from app.core.errors import QueryExecutionError
from app.db.postgres import PostgresDatabase
from app.main import create_app

if os.getenv("RUN_POSTGRES_INTEGRATION") != "1":
    pytest.skip("PostgreSQL integration test is opt-in", allow_module_level=True)


DATABASE_URL = os.environ["DATABASE_URL"]


@pytest.fixture(scope="module", autouse=True)
def seeded_database() -> None:
    seed_sql = Path("sql/001_seed.sql").read_text(encoding="utf-8")
    with psycopg.connect(DATABASE_URL, autocommit=True) as connection:
        with connection.cursor() as cursor:
            cursor.execute(seed_sql)


def test_postgres_schema_introspection_and_readonly_query() -> None:
    database = PostgresDatabase(
        database_url=DATABASE_URL,
        timeout_ms=3000,
        max_rows=50,
    )

    schema = database.introspect_schema()
    assert {"customers", "products", "orders", "order_items"} <= schema.table_names()

    rows = database.execute_readonly(
        "SELECT name, stock_quantity FROM products ORDER BY stock_quantity ASC LIMIT 3"
    )
    assert len(rows) == 3
    assert rows[0]["stock_quantity"] <= rows[-1]["stock_quantity"]


def test_api_executes_mock_generated_query_against_postgres() -> None:
    settings = Settings(
        database_url=DATABASE_URL,
        llm_provider="mock",
        query_timeout_ms=3000,
        max_result_rows=50,
    )
    with TestClient(create_app(settings)) as client:
        response = client.post(
            "/query",
            json={"question": "Which products have the lowest stock?"},
        )

    assert response.status_code == 200
    payload = response.json()
    assert payload["row_count"] > 0
    assert payload["referenced_tables"] == ["products"]
    assert "stock_quantity" in payload["rows"][0]


def test_database_transaction_rejects_mutation() -> None:
    database = PostgresDatabase(
        database_url=DATABASE_URL,
        timeout_ms=3000,
        max_rows=50,
    )

    with pytest.raises(QueryExecutionError, match="read-only|read only|PostgreSQL rejected"):
        database.execute_readonly(
            "UPDATE products SET stock_quantity = 0 WHERE id = 1 RETURNING id"
        )
