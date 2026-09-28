"""Health checks for analytics service dependencies."""

from __future__ import annotations

from typing import Any


def check_postgres_health(connection: Any) -> bool:
    """Return whether the PostgreSQL connection can execute a simple query."""
    try:
        with connection.cursor() as cursor:
            cursor.execute("SELECT 1")
            row = cursor.fetchone()

        return row == (1,)
    except Exception:
        return False


__all__ = ["check_postgres_health"]
