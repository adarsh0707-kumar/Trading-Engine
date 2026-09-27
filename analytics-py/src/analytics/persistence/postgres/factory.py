"""Factory for PostgreSQL persistence dependencies."""

from __future__ import annotations

from dataclasses import dataclass

import psycopg

from analytics.persistence.postgres.analytics import (
    PostgresAnalyticsRepository,
)
from analytics.persistence.postgres.connection import (
    create_postgres_connection,
)
from analytics.persistence.postgres.position import (
    PostgresPositionRepository,
)
from analytics.persistence.postgres.risk import PostgresRiskRepository
from analytics.persistence.postgres.trade import PostgresTradeRepository


@dataclass(frozen=True)
class PostgresRepositories:
    """PostgreSQL repositories sharing one database connection."""

    connection: psycopg.Connection
    trades: PostgresTradeRepository
    analytics: PostgresAnalyticsRepository
    positions: PostgresPositionRepository
    risk: PostgresRiskRepository

    def close(self) -> None:
        """Close the shared PostgreSQL connection."""
        self.connection.close()


def create_postgres_repositories(
    database_url: str,
) -> PostgresRepositories:
    """Create all PostgreSQL repositories from one database URL."""

    connection = create_postgres_connection(database_url)

    try:
        return PostgresRepositories(
            connection=connection,
            trades=PostgresTradeRepository(connection),
            analytics=PostgresAnalyticsRepository(connection),
            positions=PostgresPositionRepository(connection),
            risk=PostgresRiskRepository(connection),
        )
    except Exception:
        connection.close()
        raise


__all__ = [
    "PostgresRepositories",
    "create_postgres_repositories",
]