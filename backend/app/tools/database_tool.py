import logging
import re

import asyncpg

from app.config import settings
from app.tools.base import BaseTool, ToolParameter, ToolResult

logger = logging.getLogger("devagent.tools.database")

FORBIDDEN_STATEMENTS = [
    "INSERT", "UPDATE", "DELETE", "DROP", "ALTER", "CREATE",
    "TRUNCATE", "GRANT", "REVOKE", "EXECUTE", "EXEC",
]

QUERY_TIMEOUT = 10

MAX_ROWS = 100


class DatabaseQueryTool(BaseTool):
    @property
    def name(self) -> str:
        return "query_db"

    @property
    def description(self) -> str:
        return (
            "Execute a READ-ONLY SQL query against the PostgreSQL database. "
            "Only SELECT statements are allowed. Use this to look up data, "
            "count records, or analyze information in the database."
        )

    @property
    def parameters(self) -> list[ToolParameter]:
        return [
            ToolParameter(
                name="sql",
                type="string",
                description="SQL SELECT query to execute. Only SELECT statements are allowed.",
            ),
        ]

    async def execute(self, **kwargs) -> ToolResult:
        sql = kwargs.get("sql", "").strip()

        if not sql:
            return ToolResult(success=False, output="", error="Empty SQL query")

        is_safe, error = self._validate_query(sql)
        if not is_safe:
            return ToolResult(success=False, output="", error=error)

        try:
            conn = await asyncpg.connect(
                host=settings.postgres_host,
                port=settings.postgres_port,
                user=settings.postgres_user,
                password=settings.postgres_password,
                database=settings.postgres_db,
                timeout=QUERY_TIMEOUT,
            )

            try:
                rows = await conn.fetch(sql, timeout=QUERY_TIMEOUT)

                if not rows:
                    return ToolResult(
                        success=True,
                        output="Query returned 0 rows.",
                        metadata={"row_count": 0},
                    )

                truncated = len(rows) > MAX_ROWS
                rows = rows[:MAX_ROWS]

                output = self._format_results(rows, truncated)

                logger.info("📊 Query returned %d rows", len(rows))
                return ToolResult(
                    success=True,
                    output=output,
                    metadata={"row_count": len(rows), "truncated": truncated},
                )

            finally:
                await conn.close()

        except asyncpg.PostgresError as e:
            logger.error("❌ PostgreSQL error: %s", e)
            return ToolResult(
                success=False,
                output="",
                error=f"Database error: {str(e)}",
            )
        except TimeoutError:
            return ToolResult(
                success=False,
                output="",
                error=f"Query timed out after {QUERY_TIMEOUT} seconds",
            )
        except Exception as e:
            logger.error("❌ Unexpected error: %s", e)
            return ToolResult(
                success=False,
                output="",
                error=f"Unexpected error: {str(e)}",
            )

    def _validate_query(self, sql: str) -> tuple[bool, str]:
        upper_sql = sql.upper().strip()

        if not (upper_sql.startswith("SELECT") or upper_sql.startswith("WITH")):
            return False, "Only SELECT and WITH (CTE) statements are allowed"

        # No debe contener statements prohibidos fuera de strings
        # Usamos regex con word boundaries para no matchear "SELECTED" como "SELECT"+"ED"
        for stmt in FORBIDDEN_STATEMENTS:
            if re.search(rf"\b{stmt}\b", upper_sql):
                if stmt == "INSERT" or stmt == "UPDATE" or stmt == "DELETE":
                    return False, f"Statement '{stmt}' is not allowed. Only SELECT queries permitted."
                elif stmt in ("DROP", "ALTER", "CREATE", "TRUNCATE"):
                    return False, f"DDL statement '{stmt}' is not allowed."
                elif stmt in ("GRANT", "REVOKE"):
                    return False, f"Permission statement '{stmt}' is not allowed."
                elif stmt in ("EXECUTE", "EXEC"):
                    return False, f"Statement '{stmt}' is not allowed."

        if ";" in sql.rstrip(";").strip():
            return False, "Multiple statements (;) are not allowed"

        return True, ""

    def _format_results(self, rows: list, truncated: bool) -> str:
        """
        Formatea los resultados como una tabla de texto legible.

        Ejemplo:
        | id | name    | email           |
        |----|---------|-----------------|
        | 1  | Alice   | alice@test.com  |
        | 2  | Bob     | bob@test.com    |
        (2 rows)
        """
        if not rows:
            return "No results."

        columns = list(rows[0].keys())

        widths = {col: len(col) for col in columns}
        for row in rows:
            for col in columns:
                val_str = str(row[col]) if row[col] is not None else "NULL"
                widths[col] = max(widths[col], min(len(val_str), 50))  # Max 50 chars

        header = " | ".join(col.ljust(widths[col]) for col in columns)
        separator = "-|-".join("-" * widths[col] for col in columns)

        lines = [header, separator]
        for row in rows:
            values = []
            for col in columns:
                val = row[col]
                val_str = str(val) if val is not None else "NULL"
                if len(val_str) > 50:
                    val_str = val_str[:47] + "..."
                values.append(val_str.ljust(widths[col]))
            lines.append(" | ".join(values))

        footer = f"({len(rows)} rows"
        if truncated:
            footer += f", truncated to {MAX_ROWS}"
        footer += ")"
        lines.append(footer)

        return "\n".join(lines)