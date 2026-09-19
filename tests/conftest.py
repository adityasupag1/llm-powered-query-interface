from __future__ import annotations

import pytest

from app.db.schema import ColumnInfo, DatabaseSchema, TableInfo


@pytest.fixture
def demo_schema() -> DatabaseSchema:
    return DatabaseSchema(
        tables=(
            TableInfo(
                name="customers",
                columns=(
                    ColumnInfo("id", "bigint", False),
                    ColumnInfo("name", "text", False),
                    ColumnInfo("state", "text", False),
                ),
            ),
            TableInfo(
                name="orders",
                columns=(
                    ColumnInfo("id", "bigint", False),
                    ColumnInfo("customer_id", "bigint", False),
                    ColumnInfo("status", "text", False),
                ),
            ),
        )
    )
