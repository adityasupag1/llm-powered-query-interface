from __future__ import annotations

from app.db.schema import DatabaseSchema


def build_sql_prompt(question: str, schema: DatabaseSchema, max_rows: int) -> str:
    return f"""You translate user questions into safe PostgreSQL SELECT queries.

DATABASE SCHEMA:
{schema.to_prompt_text()}

RULES:
- Return exactly one PostgreSQL query and nothing else.
- Read data only. Never use INSERT, UPDATE, DELETE, DROP, ALTER, TRUNCATE, CREATE, GRANT, REVOKE, COPY, CALL, or transaction-control statements.
- Use only tables and columns present in the schema.
- Prefer explicit JOIN conditions.
- Do not query system schemas.
- Cap result sets at {max_rows} rows or fewer.
- If aggregation is requested, return useful labels for calculated columns.

USER QUESTION:
{question}

SQL:"""
