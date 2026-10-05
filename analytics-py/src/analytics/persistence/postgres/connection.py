"""PostgreSQL connection factory."""

from __future__ import annotations

import psycopg


def create_postgres_connection(
    database_url: str,
) -> psycopg.Connection:
    """Create a PostgreSQL connection from a database URL."""

    if not isinstance(database_url, str):
        raise TypeError("database_url must be a string")

    if not database_url.strip():
        raise ValueError("database_url must not be empty")

    return psycopg.connect(
        database_url,
        autocommit=True,
    )


__all__ = ["create_postgres_connection"]