"""Health checks for analytics service dependencies."""

from __future__ import annotations

import logging
from typing import Any


logger = logging.getLogger(__name__)


def check_postgres_health(connection: Any) -> bool:
    """Return whether the PostgreSQL connection can execute a simple query."""
    try:
        with connection.cursor() as cursor:
            cursor.execute("SELECT 1")
            row = cursor.fetchone()

        return row == (1,)
    except Exception as exc:
        # Keep the check non-raising for readiness probes, but retain useful
        # diagnostics without logging connection strings or credentials.
        logger.warning(
            "postgres_health_check_failed error_type=%s error=%s",
            type(exc).__name__,
            str(exc),
        )
        return False


__all__ = ["check_postgres_health"]
