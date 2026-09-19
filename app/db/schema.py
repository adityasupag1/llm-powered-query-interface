from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class ColumnInfo:
    name: str
    data_type: str
    nullable: bool


@dataclass(frozen=True)
class TableInfo:
    name: str
    columns: tuple[ColumnInfo, ...]


@dataclass(frozen=True)
class DatabaseSchema:
    tables: tuple[TableInfo, ...]

    def table_names(self) -> set[str]:
        return {table.name for table in self.tables}

    def columns_for(self, table_name: str) -> set[str]:
        for table in self.tables:
            if table.name == table_name:
                return {column.name for column in table.columns}
        return set()

    def to_prompt_text(self) -> str:
        lines: list[str] = []
        for table in self.tables:
            columns = ", ".join(
                f"{col.name} {col.data_type}{'' if col.nullable else ' NOT NULL'}"
                for col in table.columns
            )
            lines.append(f"- {table.name}({columns})")
        return "\n".join(lines)
