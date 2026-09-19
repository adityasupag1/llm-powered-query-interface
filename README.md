# LLM-Powered Query Interface

[![CI](https://github.com/adityasupag1/llm-powered-query-interface/actions/workflows/ci.yml/badge.svg)](https://github.com/adityasupag1/llm-powered-query-interface/actions/workflows/ci.yml)
![Python](https://img.shields.io/badge/Python-3.11%2B-blue)
![FastAPI](https://img.shields.io/badge/FastAPI-PostgreSQL-informational)

## Live demo

- **Interactive API docs:** https://llm-powered-query-interface-pmmi.onrender.com/docs
- **Health check:** https://llm-powered-query-interface-pmmi.onrender.com/health
- **Live schema:** https://llm-powered-query-interface-pmmi.onrender.com/schema

> The free Render instance may take up to about 50 seconds to wake after inactivity.


A production-style FastAPI service that translates natural-language questions into **read-only PostgreSQL queries**, validates the generated SQL against the live database schema, executes it with safety limits, and returns structured JSON results.

The project is designed to demonstrate the engineering required to put an LLM between users and structured data safely. It is more than a text-to-SQL prompt: generated queries pass through schema checks, statement restrictions, row limits, a read-only transaction, and a database execution timeout before results are returned.

## Why this exists

Business users often know the question they want answered but do not know SQL. This service provides an "ask your database" API for questions such as:

- "Which products generated the most revenue?"
- "Who are the top five customers by total spend?"
- "Which products have the lowest stock?"

A real LLM can be enabled through an OpenAI-compatible API. A deterministic local provider is included so the entire project can be developed and demonstrated without an API key.

## Architecture

```text
Client question
     |
     v
FastAPI /query
     |
     v
Schema introspection ------> PostgreSQL information_schema
     |
     v
Schema-aware prompt builder
     |
     v
LLM provider (mock or OpenAI-compatible)
     |
     v
SQL safety validator
  - one statement only
  - SELECT/read-only only
  - public schema only
  - known tables/columns
  - fixed LIMIT
     |
     v
Read-only PostgreSQL transaction
  - statement timeout
  - result-row cap
     |
     v
Structured JSON response
```

## Core features

- FastAPI REST API with generated OpenAPI documentation
- live PostgreSQL schema introspection
- schema-aware prompt generation
- provider abstraction for deterministic local development or OpenAI-compatible LLM APIs
- SQL parsing and validation with `sqlglot`
- destructive/mutating statement rejection
- multiple-statement rejection
- system-schema access rejection
- table and qualified-column validation against the live schema
- maximum result limit enforcement
- PostgreSQL `READ ONLY` transaction execution
- PostgreSQL `statement_timeout` protection
- structured application errors
- Docker and Docker Compose setup
- realistic e-commerce seed dataset
- unit, service, and API tests
- Ruff linting and GitHub Actions matrix CI for Python 3.11, 3.12, and 3.13
- live PostgreSQL integration tests in CI
- Docker image build verification in CI

## Quick start with Docker

```bash
git clone https://github.com/adityasupag1/llm-powered-query-interface.git
cd llm-powered-query-interface
cp .env.example .env
docker compose up --build
```

The API will be available at `http://localhost:8000` and interactive documentation at `http://localhost:8000/docs`.

The default `mock` provider requires no external API key.

## Example request

```bash
curl -X POST http://localhost:8000/query \
  -H 'Content-Type: application/json' \
  -d '{"question":"Which products generated the most revenue?"}'
```

## Example response

```json
{
  "question": "Which products generated the most revenue?",
  "sql": "SELECT p.name, SUM(oi.quantity * oi.unit_price) AS revenue ... LIMIT 10",
  "referenced_tables": ["order_items", "orders", "products"],
  "generation_ms": 0.15,
  "rows": [
    {
      "name": "Mechanical Keyboard",
      "revenue": 13497.00
    }
  ],
  "row_count": 5,
  "execution_ms": 2.41
}
```

The API returns the validated SQL as part of the response so generated behavior can be inspected and audited.

## API endpoints

| Method | Endpoint | Purpose |
| --- | --- | --- |
| `GET` | `/health` | API/database health status and active LLM provider |
| `GET` | `/schema` | Read the database schema visible to the query service |
| `POST` | `/query/preview` | Generate and validate SQL without executing it |
| `POST` | `/query` | Generate, validate, execute, and return query results |

## Using a real LLM

The default provider is deterministic:

```env
LLM_PROVIDER=mock
```

For an OpenAI-compatible endpoint:

```env
LLM_PROVIDER=openai-compatible
LLM_MODEL=gpt-4.1-mini
LLM_API_KEY=your-key
LLM_BASE_URL=https://api.openai.com/v1
```

Provider output is treated as untrusted and must pass SQL validation before execution.

## Safety model

LLM-generated SQL must never be executed directly. This project uses defense in depth:

1. Prompt requests exactly one read-only query.
2. SQL is parsed into an AST.
3. Mutating and DDL statements are rejected.
4. Multiple statements are rejected.
5. System/non-public schemas are rejected.
6. Tables are checked against the live schema.
7. Qualified columns are validated.
8. Result limits are injected or clamped.
9. PostgreSQL executes in a `READ ONLY` transaction.
10. PostgreSQL enforces a statement timeout.
11. API enforces a hard row cap.

This is suitable for demos/internal analytics, but it is not a complete multi-tenant security boundary.

## Local development

```bash
docker compose up -d db
python -m venv .venv
source .venv/bin/activate
python -m pip install -e ".[dev]"
uvicorn app.main:app --reload
```

## Test strategy

The CI pipeline validates three layers:

- **Unit/service tests** for prompting, provider behavior, SQL validation, and query orchestration
- **API tests** for request validation and structured responses
- **Live PostgreSQL integration tests** for schema introspection, actual query execution, API-to-database flow, and database-level read-only enforcement

The workflow also builds the production Docker image to catch container packaging failures.

Run checks locally:

```bash
ruff check .
pytest --cov=app --cov-report=term-missing
```

## Project structure

```text
.
├── app/
│   ├── api/
│   ├── core/
│   ├── db/
│   ├── llm/
│   ├── services/
│   └── main.py
├── sql/001_seed.sql
├── tests/
├── Dockerfile
├── docker-compose.yml
├── pyproject.toml
└── .github/workflows/ci.yml
```

## Design decisions

**Schema is discovered at runtime.** Prompting and validation use the actual public PostgreSQL schema.

**Generation and execution are separate.** `/query/preview` lets generated SQL be inspected without executing it.

**Provider output is untrusted.** The model proposes SQL; application code decides whether it is safe.

**Database restrictions are the final guardrail.** Accepted queries still execute in a read-only transaction with a timeout.

## Limitations

- semantic correctness still depends on the model and schema quality
- ambiguous business definitions require a semantic/catalog layer
- large schemas benefit from schema retrieval
- production should use a dedicated least-privilege DB user
- multi-tenant deployments need authorization rules
- sensitive columns should be filtered or masked
