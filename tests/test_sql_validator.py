from __future__ import annotations

import pytest

from app.core.errors import SQLValidationError
from app.services.sql_validator import SQLSafetyValidator


def test_accepts_readonly_select_and_adds_limit(demo_schema):
    validator = SQLSafetyValidator(max_rows=100)
    result = validator.validate("SELECT id, name FROM customers", demo_schema)
    assert result.sql == "SELECT id, name FROM customers LIMIT 100"
    assert result.referenced_tables == ("customers",)


def test_clamps_excessive_limit(demo_schema):
    validator = SQLSafetyValidator(max_rows=50)
    result = validator.validate("SELECT id FROM customers LIMIT 1000", demo_schema)
    assert result.sql.endswith("LIMIT 50")


@pytest.mark.parametrize(
    "sql",
    [
        "DELETE FROM customers",
        "UPDATE customers SET name = 'x'",
        "DROP TABLE customers",
        "INSERT INTO customers (name) VALUES ('x')",
    ],
)
def test_rejects_mutating_statements(sql, demo_schema):
    validator = SQLSafetyValidator(max_rows=100)
    with pytest.raises(SQLValidationError, match="read-only|SELECT"):
        validator.validate(sql, demo_schema)


def test_rejects_multiple_statements(demo_schema):
    validator = SQLSafetyValidator(max_rows=100)
    with pytest.raises(SQLValidationError, match="Exactly one"):
        validator.validate("SELECT id FROM customers; SELECT id FROM orders", demo_schema)


def test_rejects_unknown_table(demo_schema):
    validator = SQLSafetyValidator(max_rows=100)
    with pytest.raises(SQLValidationError, match="unknown table"):
        validator.validate("SELECT id FROM payments", demo_schema)


def test_rejects_unknown_qualified_column(demo_schema):
    validator = SQLSafetyValidator(max_rows=100)
    with pytest.raises(SQLValidationError, match="unknown column"):
        validator.validate("SELECT c.email FROM customers AS c", demo_schema)


def test_accepts_join_and_projection_alias(demo_schema):
    validator = SQLSafetyValidator(max_rows=100)
    result = validator.validate(
        """
        SELECT c.name, COUNT(o.id) AS order_count
        FROM customers c
        JOIN orders o ON o.customer_id = c.id
        GROUP BY c.id, c.name
        ORDER BY order_count DESC
        """,
        demo_schema,
    )
    assert "ORDER BY order_count DESC" in result.sql
    assert result.referenced_tables == ("customers", "orders")


def test_rejects_system_schema(demo_schema):
    validator = SQLSafetyValidator(max_rows=100)
    with pytest.raises(SQLValidationError, match="public application schema"):
        validator.validate("SELECT tablename FROM pg_catalog.pg_tables", demo_schema)
