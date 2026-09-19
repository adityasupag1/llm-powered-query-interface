from __future__ import annotations

from dataclasses import dataclass

from sqlglot import exp, parse
from sqlglot.errors import ParseError

from app.core.errors import SQLValidationError
from app.db.schema import DatabaseSchema


@dataclass(frozen=True)
class ValidatedSQL:
    sql: str
    referenced_tables: tuple[str, ...]


class SQLSafetyValidator:
    _blocked_nodes = tuple(
        filter(
            None,
            (
                getattr(exp, name, None)
                for name in (
                    "Insert",
                    "Update",
                    "Delete",
                    "Create",
                    "Drop",
                    "Alter",
                    "Command",
                    "Merge",
                    "Transaction",
                )
            ),
        )
    )


    def __init__(self, max_rows: int):
        self.max_rows = max_rows

    def validate(self, sql: str, schema: DatabaseSchema) -> ValidatedSQL:
        cleaned = sql.strip().rstrip(";").strip()
        if not cleaned:
            raise SQLValidationError("Generated SQL is empty")

        try:
            statements = parse(cleaned, read="postgres")
        except ParseError as exc:
            raise SQLValidationError("Generated SQL could not be parsed") from exc

        if len(statements) != 1:
            raise SQLValidationError("Exactly one SQL statement is allowed")

        expression = statements[0]
        if any(expression.find(node_type) is not None for node_type in self._blocked_nodes):
            raise SQLValidationError("Only read-only SELECT queries are allowed")

        if not isinstance(expression, (exp.Select, exp.Union, exp.Intersect, exp.Except)):
            raise SQLValidationError("Only SELECT queries are allowed")

        for table in expression.find_all(exp.Table):
            catalog = table.catalog
            db = table.db
            if catalog or (db and db.lower() != "public"):
                raise SQLValidationError("Only the public application schema may be queried")

        cte_names = {cte.alias_or_name for cte in expression.find_all(exp.CTE)}
        referenced = {
            table.name
            for table in expression.find_all(exp.Table)
            if table.name not in cte_names
        }

        unknown_tables = sorted(referenced - schema.table_names())
        if unknown_tables:
            raise SQLValidationError(
                "Query references unknown table(s): " + ", ".join(unknown_tables)
            )

        aliases: dict[str, str] = {}
        for table in expression.find_all(exp.Table):
            if table.name in cte_names:
                continue
            aliases[table.alias_or_name] = table.name
            aliases[table.name] = table.name

        for column in expression.find_all(exp.Column):
            name = column.name
            qualifier = column.table
            if name == "*":
                continue
            if qualifier:
                table_name = aliases.get(qualifier)
                if table_name and name not in schema.columns_for(table_name):
                    raise SQLValidationError(
                        f"Query references unknown column: {qualifier}.{name}"
                    )
            else:
                matching_tables = [
                    table_name
                    for table_name in referenced
                    if name in schema.columns_for(table_name)
                ]
                # Unqualified computed aliases are valid in ORDER BY/GROUP BY.
                if not matching_tables and not self._is_projection_alias(expression, name):
                    raise SQLValidationError(f"Query references unknown column: {name}")

        limited = self._enforce_limit(expression)
        return ValidatedSQL(
            sql=limited.sql(dialect="postgres"),
            referenced_tables=tuple(sorted(referenced)),
        )

    def _is_projection_alias(self, expression: exp.Expression, name: str) -> bool:
        aliases = {
            item.alias
            for select in expression.find_all(exp.Select)
            for item in select.expressions
            if item.alias
        }
        return name in aliases

    def _enforce_limit(self, expression: exp.Expression) -> exp.Expression:
        root = expression.copy()
        limit = root.args.get("limit")
        if limit is None:
            return root.limit(self.max_rows)

        value = limit.expression
        if isinstance(value, exp.Literal) and value.is_int:
            requested = int(value.this)
            if requested > self.max_rows:
                return root.limit(self.max_rows)
            return root

        raise SQLValidationError("LIMIT must be a fixed integer")
