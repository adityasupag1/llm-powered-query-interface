from __future__ import annotations

from app.db.schema import ColumnInfo, DatabaseSchema, TableInfo
from app.services.query_service import QueryService
from app.services.sql_validator import SQLSafetyValidator


class FakeDatabase:
    def __init__(self):
        self.executed_sql = None

    def introspect_schema(self):
        return DatabaseSchema(
            tables=(
                TableInfo(
                    "products",
                    (
                        ColumnInfo("id", "bigint", False),
                        ColumnInfo("name", "text", False),
                        ColumnInfo("stock_quantity", "integer", False),
                    ),
                ),
            )
        )

    def execute_readonly(self, sql):
        self.executed_sql = sql
        return [{"id": 1, "name": "Keyboard", "stock_quantity": 3}]


class FakeGenerator:
    def generate_sql(self, _prompt):
        return "SELECT id, name, stock_quantity FROM products ORDER BY stock_quantity"


def test_service_validates_then_executes_query():
    database = FakeDatabase()
    service = QueryService(
        database=database,
        generator=FakeGenerator(),
        validator=SQLSafetyValidator(max_rows=20),
        max_rows=20,
    )
    result = service.execute("What is low in stock?")
    assert result.row_count == 1
    assert result.rows[0]["name"] == "Keyboard"
    assert database.executed_sql.endswith("LIMIT 20")
