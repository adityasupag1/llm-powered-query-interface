from app.db.schema import ColumnInfo, DatabaseSchema, TableInfo
from app.llm.mock import MockSQLGenerator
from app.services.prompt_builder import build_sql_prompt


def schema() -> DatabaseSchema:
    return DatabaseSchema(
        tables=(
            TableInfo("customers", (ColumnInfo("id", "bigint", False), ColumnInfo("name", "text", False))),
            TableInfo("orders", (ColumnInfo("id", "bigint", False), ColumnInfo("customer_id", "bigint", False), ColumnInfo("status", "text", False))),
            TableInfo("order_items", (ColumnInfo("order_id", "bigint", False), ColumnInfo("product_id", "bigint", False), ColumnInfo("quantity", "integer", False), ColumnInfo("unit_price", "numeric", False))),
            TableInfo("products", (ColumnInfo("id", "bigint", False), ColumnInfo("name", "text", False), ColumnInfo("category", "text", False), ColumnInfo("unit_price", "numeric", False), ColumnInfo("stock_quantity", "integer", False))),
        )
    )


def test_mock_provider_generates_revenue_query():
    prompt = build_sql_prompt("Which products generated the most revenue?", schema(), 100)
    sql = MockSQLGenerator().generate_sql(prompt)
    assert "SUM" in sql
    assert "products" in sql
    assert "revenue" in sql
