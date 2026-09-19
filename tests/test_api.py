from __future__ import annotations

from dataclasses import dataclass

from fastapi.testclient import TestClient

from app.core.config import Settings
from app.main import create_app
from app.services.query_service import QueryPreview, QueryResult


class FakeDatabase:
    def healthcheck(self):
        return True

    def introspect_schema(self):
        from app.db.schema import ColumnInfo, DatabaseSchema, TableInfo

        return DatabaseSchema(
            tables=(TableInfo("products", (ColumnInfo("id", "bigint", False),)),)
        )


class FakeQueryService:
    def preview(self, question):
        return QueryPreview(question, "SELECT id FROM products LIMIT 10", ("products",), 1.2)

    def execute(self, question):
        return QueryResult(
            question,
            "SELECT id FROM products LIMIT 10",
            [{"id": 1}],
            1,
            ("products",),
            1.2,
            2.3,
        )


@dataclass
class FakeServices:
    settings: Settings
    database: FakeDatabase
    query_service: FakeQueryService


def client():
    settings = Settings(llm_provider="mock")
    app = create_app(settings)
    app.state.services = FakeServices(settings, FakeDatabase(), FakeQueryService())
    return TestClient(app)


def test_health_endpoint():
    response = client().get("/health")
    assert response.status_code == 200
    assert response.json() == {"status": "ok", "database": "ok", "llm_provider": "mock"}


def test_query_endpoint():
    response = client().post("/query", json={"question": "Show products"})
    assert response.status_code == 200
    payload = response.json()
    assert payload["row_count"] == 1
    assert payload["referenced_tables"] == ["products"]


def test_question_validation():
    response = client().post("/query", json={"question": "x"})
    assert response.status_code == 422
