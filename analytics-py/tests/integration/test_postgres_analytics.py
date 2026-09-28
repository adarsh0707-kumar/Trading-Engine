"""Integration tests for PostgreSQL analytics persistence."""

from __future__ import annotations

import os
from datetime import datetime, timedelta, timezone
from decimal import Decimal
from pathlib import Path
from uuid import uuid4

import psycopg
import pytest
from psycopg import sql

from analytics.models import AnalyticsResult
from analytics.persistence.migrations import MigrationRunner
from analytics.persistence.postgres import PostgresAnalyticsRepository


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
                sql.SQL(
                    "DROP SCHEMA IF EXISTS {} CASCADE"
                ).format(
                    sql.Identifier(schema_name)
                )
            )

        connection.close()


@pytest.fixture()
def migrated_connection(postgres_connection):
    """Apply the real PostgreSQL migrations before each test."""

    runner = MigrationRunner(
        postgres_connection,
        MIGRATIONS_PATH,
    )

    runner.run()
    postgres_connection.commit()

    return postgres_connection


@pytest.fixture()
def repository(migrated_connection):
    """Return a PostgreSQL analytics repository."""

    return PostgresAnalyticsRepository(
        migrated_connection
    )


def _analytics(
    *,
    event_id: str,
    symbol: str = "BTCUSDT",
    price: str = "65000.25",
    vwap: str | None = "64999.50",
    sma: str | None = "64980.00",
    ema: str | None = "64990.00",
    position: int = 2,
    realized_pnl: str = "100.25",
    unrealized_pnl: str = "50.75",
    equity: str = "10151.00",
    peak_equity: str = "10200.00",
    drawdown: str = "49.00",
    timestamp: datetime | None = None,
) -> AnalyticsResult:
    """Build a deterministic analytics result."""

    return AnalyticsResult(
        event_id=event_id,
        event_type="ANALYTICS_UPDATE",
        symbol=symbol,
        price=Decimal(price),
        vwap=Decimal(vwap) if vwap is not None else None,
        sma=Decimal(sma) if sma is not None else None,
        ema=Decimal(ema) if ema is not None else None,
        position=position,
        realized_pnl=Decimal(realized_pnl),
        unrealized_pnl=Decimal(unrealized_pnl),
        equity=Decimal(equity),
        peak_equity=Decimal(peak_equity),
        drawdown=Decimal(drawdown),
        timestamp=timestamp
        or datetime(
            2026,
            9,
            14,
            12,
            0,
            tzinfo=timezone.utc,
        ),
    )


def test_repository_saves_and_reads_analytics(repository) -> None:
    """An analytics result survives a PostgreSQL round trip."""

    result = _analytics(
        event_id="analytics-pg-001",
    )

    repository.save(result)
    repository._connection.commit()

    loaded = repository.get_by_event_id(
        result.event_id
    )

    assert loaded == result


def test_repository_returns_none_for_unknown_event(repository) -> None:
    """An unknown analytics event returns None."""

    assert repository.get_by_event_id(
        "analytics-pg-missing"
    ) is None


def test_repository_lists_by_symbol(repository) -> None:
    """Analytics results are returned in timestamp order."""

    base_time = datetime(
        2026,
        9,
        14,
        12,
        0,
        tzinfo=timezone.utc,
    )

    first = _analytics(
        event_id="analytics-pg-symbol-001",
        symbol="ETHUSDT",
        timestamp=base_time + timedelta(seconds=2),
    )

    second = _analytics(
        event_id="analytics-pg-symbol-002",
        symbol="ETHUSDT",
        timestamp=base_time + timedelta(seconds=1),
    )

    other_symbol = _analytics(
        event_id="analytics-pg-symbol-003",
        symbol="BTCUSDT",
        timestamp=base_time,
    )

    for result in (first, second, other_symbol):
        repository.save(result)

    repository._connection.commit()

    results = repository.list_by_symbol("ETHUSDT")

    assert results == (second, first)


def test_repository_lists_by_time_range(repository) -> None:
    """Analytics results can be queried using an inclusive range."""

    base_time = datetime(
        2026,
        9,
        14,
        13,
        0,
        tzinfo=timezone.utc,
    )

    before = _analytics(
        event_id="analytics-pg-range-001",
        timestamp=base_time - timedelta(seconds=1),
    )

    inside = _analytics(
        event_id="analytics-pg-range-002",
        timestamp=base_time,
    )

    after = _analytics(
        event_id="analytics-pg-range-003",
        timestamp=base_time + timedelta(seconds=1),
    )

    for result in (before, inside, after):
        repository.save(result)

    repository._connection.commit()

    results = repository.list_by_time_range(
        base_time,
        base_time,
    )

    assert results == (inside,)


def test_repository_rejects_reversed_time_range(repository) -> None:
    """A reversed time range is rejected."""

    start = datetime(
        2026,
        9,
        14,
        14,
        0,
        tzinfo=timezone.utc,
    )

    end = start - timedelta(seconds=1)

    with pytest.raises(ValueError, match="start must not be after end"):
        repository.list_by_time_range(start, end)


def test_repository_upserts_existing_event_id(repository) -> None:
    """Saving an existing event_id updates the derived result."""

    original = _analytics(
        event_id="analytics-pg-upsert-001",
        price="100.00",
        position=1,
        realized_pnl="10.00",
    )

    updated = _analytics(
        event_id="analytics-pg-upsert-001",
        price="125.50",
        position=5,
        realized_pnl="75.00",
    )

    repository.save(original)
    repository._connection.commit()

    repository.save(updated)
    repository._connection.commit()

    loaded = repository.get_by_event_id(
        updated.event_id
    )

    assert loaded == updated


def test_repository_preserves_nullable_indicators(repository) -> None:
    """Optional indicators remain NULL when not available."""

    result = _analytics(
        event_id="analytics-pg-nullable-001",
        vwap=None,
        sma=None,
        ema=None,
    )

    repository.save(result)
    repository._connection.commit()

    loaded = repository.get_by_event_id(
        result.event_id
    )

    assert loaded == result


def test_database_enforces_analytics_constraints(
    migrated_connection,
) -> None:
    """PostgreSQL enforces analytics-result constraints."""

    with migrated_connection.cursor() as cursor:
        with pytest.raises(psycopg.errors.CheckViolation):
            cursor.execute(
                """
                INSERT INTO analytics_results (
                    event_id,
                    event_type,
                    symbol,
                    price,
                    vwap,
                    sma,
                    ema,
                    position,
                    realized_pnl,
                    unrealized_pnl,
                    equity,
                    peak_equity,
                    drawdown,
                    timestamp
                )
                VALUES (
                    'analytics-pg-invalid-001',
                    'ANALYTICS_UPDATE',
                    'BTCUSDT',
                    0,
                    NULL,
                    NULL,
                    NULL,
                    0,
                    0,
                    0,
                    10000,
                    10000,
                    0,
                    CURRENT_TIMESTAMP
                )
                """
            )

    migrated_connection.rollback()

    with migrated_connection.cursor() as cursor:
        cursor.execute(
            """
            SELECT COUNT(*)
            FROM analytics_results
            WHERE event_id = 'analytics-pg-invalid-001'
            """
        )

        count = cursor.fetchone()[0]

    assert count == 0
