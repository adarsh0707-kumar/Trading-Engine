"""End-to-end tests for application-level PostgreSQL persistence."""

from __future__ import annotations

import os
from pathlib import Path
from uuid import uuid4

import psycopg
import pytest
from psycopg import sql

from analytics.config.settings import Settings
from analytics.main import AnalyticsService
from analytics.persistence.migrations import MigrationRunner
from analytics.persistence.postgres import (
    PostgresAnalyticsRepository,
    PostgresPositionRepository,
    PostgresRepositories,
    PostgresRiskRepository,
    PostgresTradeRepository,
)


DATABASE_URL_ENV = "TRADING_ENGINE_TEST_DATABASE_URL"
MIGRATIONS_PATH = (
    Path(__file__).resolve().parents[2] / "migrations"
)


def _database_url() -> str:
    """Return the configured PostgreSQL integration-test URL."""

    value = os.getenv(DATABASE_URL_ENV)

    if not value:
        pytest.skip(
            f"{DATABASE_URL_ENV} is not configured"
        )

    return value


@pytest.fixture(scope="module")
def postgres_connection():
    """Create an isolated PostgreSQL schema for this test module."""

    connection = psycopg.connect(_database_url())
    schema_name = f"test_{uuid4().hex}"

    try:
        with connection.transaction():
            with connection.cursor() as cursor:
                cursor.execute(
                    sql.SQL("CREATE SCHEMA {}").format(
                        sql.Identifier(schema_name)
                    )
                )

        with connection.cursor() as cursor:
            cursor.execute(
                "SELECT pg_catalog.set_config(%s, %s, false)",
                ("search_path", f'"{schema_name}"'),
            )

        connection.commit()

        yield connection

    finally:
        connection.rollback()
        connection.autocommit = True

        with connection.cursor() as cursor:
            cursor.execute(
                sql.SQL("DROP SCHEMA IF EXISTS {} CASCADE").format(
                    sql.Identifier(schema_name)
                )
            )

        connection.close()


@pytest.fixture(scope="module")
def repositories(postgres_connection) -> PostgresRepositories:
    """Create real PostgreSQL repositories in the isolated schema."""

    runner = MigrationRunner(
        postgres_connection,
        MIGRATIONS_PATH,
    )

    runner.run()
    postgres_connection.commit()

    return PostgresRepositories(
        connection=postgres_connection,
        trades=PostgresTradeRepository(postgres_connection),
        analytics=PostgresAnalyticsRepository(postgres_connection),
        positions=PostgresPositionRepository(postgres_connection),
        risk=PostgresRiskRepository(postgres_connection),
    )


def test_trade_flows_from_transport_to_postgresql(
    repositories: PostgresRepositories,
) -> None:
    """A real transport trade is processed and persisted end to end."""

    service = AnalyticsService(
        Settings(),
        repositories=repositories,
        publish_sink=lambda _payload: None,
    )

    service._handle_message(
        '{"type":"TRADE",'
        '"request_id":"event-e2e-001",'
        '"timestamp":"2026-09-27T10:00:00+00:00",'
        '"payload":"{'
        '\\"symbol\\":\\"AAPL\\",'
        '\\"price\\":\\"100\\",'
        '\\"quantity\\":8,'
        '\\"taker_order_id\\":\\"order-taker-001\\",'
        '\\"maker_order_id\\":\\"order-maker-001\\",'
        '\\"taker_side\\":\\"BUY\\"'
        '}"'
        '}',
    )

    trade = repositories.trades.get_by_id(
        "event-e2e-001",
    )

    analytics_results = repositories.analytics.list_by_symbol(
        "AAPL",
    )

    position = repositories.positions.get_by_symbol(
        symbol="AAPL",
    )

    risk_state = repositories.risk.get_latest_state(
        symbol="AAPL",
    )

    risk_events = repositories.risk.list_events(
        symbol="AAPL",
    )

    assert trade is not None
    assert trade.event_id == "event-e2e-001"
    assert trade.symbol == "AAPL"
    assert trade.price == 100
    assert trade.quantity == 8
    assert trade.taker_side == "BUY"

    assert len(analytics_results) == 1

    analytics = analytics_results[0]

    assert analytics.event_type == "ANALYTICS_UPDATE"
    assert analytics.symbol == "AAPL"
    assert analytics.price == 100
    assert analytics.position == 8

    assert position is not None
    assert position.position == 8
    assert position.average_entry_price == 100

    assert risk_state == position
    assert risk_events == ()
