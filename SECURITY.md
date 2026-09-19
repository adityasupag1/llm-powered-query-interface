# Security notes

This project treats all LLM-generated SQL as untrusted input.

The application rejects non-read-only statements, multiple statements, access to non-public schemas, unknown application tables, and invalid qualified columns. It also enforces a result limit and runs accepted SQL in a PostgreSQL read-only transaction with a statement timeout.

For production use, create a dedicated database role that has only the minimum required `SELECT` privileges. Do not connect the service with a database owner, migration user, or superuser account. Network access to PostgreSQL should be restricted to the application environment.

Do not expose sensitive schema metadata or result columns to an external LLM provider without reviewing the applicable privacy and data-handling requirements. Multi-tenant systems need an authorization layer independent of SQL validation.
