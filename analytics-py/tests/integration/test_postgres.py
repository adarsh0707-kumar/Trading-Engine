"""Integration tests for PostgreSQL persistence."""

from __future__ import annotations

import os
from datetime import datetime, timedelta, timezone
from decimal import Decimal
from pathlib import Path
from uuid import uuid4

import psycopg
import pytest
from psycopg import sql

from analytics.models import Trade
from analytics.persistence.migrations import MigrationRunner
from analytics.persistence.postgres import PostgresTradeRepository


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


@pytest.fixture()
def migrated_connection(postgres_connection):
    """Apply the real PostgreSQL migrations before a test."""

    runner = MigrationRunner(
        postgres_connection,
        MIGRATIONS_PATH,
    )

    runner.run()
    postgres_connection.commit()

    return postgres_connection

@pytest.fixture()
def repository(migrated_connection):
    """Return a PostgreSQL trade repository backed by the test database."""

    return PostgresTradeRepository(migrated_connection)


def _trade(
    *,
    trade_id: str,
    event_id: str,
    symbol: str = "BTCUSDT",
    price: str = "65000.25",
    quantity: int = 2,
    timestamp: datetime | None = None,
    taker_side: str = "BUY",
    buy_order_id: str | None = "buy-001",
    sell_order_id: str | None = "sell-001",
    taker_order_id: str | None = "taker-001",
    maker_order_id: str | None = "maker-001",
) -> Trade:
    """Build a deterministic trade for integration tests."""

    return Trade(
        event_id=event_id,
        event_type="TRADE",
        trade_id=trade_id,
        symbol=symbol,
        price=Decimal(price),
        quantity=quantity,
        timestamp=timestamp
        or datetime(
            2026,
            9,
            14,
            12,
            0,
            tzinfo=timezone.utc,
        ),
        taker_side=taker_side,
        buy_order_id=buy_order_id,
        sell_order_id=sell_order_id,
        taker_order_id=taker_order_id,
        maker_order_id=maker_order_id,
    )


def test_real_migration_creates_expected_schema(
    migrated_connection,
) -> None:
    """The real migration creates the trade store and indexes."""

    with migrated_connection.cursor() as cursor:
        cursor.execute(
            """
            SELECT version
            FROM schema_migrations
            ORDER BY version
            """
        )
        migration_versions = cursor.fetchall()

        cursor.execute(
            """
            SELECT column_name
            FROM information_schema.columns
            WHERE table_schema = current_schema()
              AND table_name = 'trades'
            ORDER BY ordinal_position
            """
        )
        columns = [row[0] for row in cursor.fetchall()]

        cursor.execute(
            """
            SELECT indexname
            FROM pg_indexes
            WHERE schemaname = current_schema()
              AND tablename = 'trades'
            ORDER BY indexname
            """
        )
        indexes = {row[0] for row in cursor.fetchall()}

    assert migration_versions == [("001",)]

    assert columns == [
        "trade_id",
        "event_id",
        "event_type",
        "symbol",
        "price",
        "quantity",
        "timestamp",
        "taker_side",
        "buy_order_id",
        "sell_order_id",
        "taker_order_id",
        "maker_order_id",
    ]

    assert indexes == {
        "trades_pkey",
        "trades_event_id_key",
        "idx_trades_symbol_timestamp",
        "idx_trades_timestamp",
    }


def test_migration_is_idempotent(migrated_connection) -> None:
    """Running migrations again does not reapply existing migrations."""

    runner = MigrationRunner(
        migrated_connection,
        MIGRATIONS_PATH,
    )

    applied = runner.run()

    migrated_connection.commit()

    assert applied == ()

    with migrated_connection.cursor() as cursor:
        cursor.execute(
            """
            SELECT COUNT(*)
            FROM schema_migrations
            """
        )
        count = cursor.fetchone()[0]

    assert count == 1


def test_repository_saves_and_reads_trade(repository) -> None:
    """A trade survives a PostgreSQL round trip."""

    trade = _trade(
        trade_id="trade-pg-001",
        event_id="event-pg-001",
    )

    repository.save(trade)
    repository._connection.commit()

    loaded = repository.get_by_id(trade.trade_id)

    assert loaded == trade


def test_repository_lists_trades_by_symbol(repository) -> None:
    """Trades are returned by symbol in timestamp order."""

    base_time = datetime(
        2026,
        9,
        14,
        12,
        0,
        tzinfo=timezone.utc,
    )

    first = _trade(
        trade_id="trade-pg-symbol-001",
        event_id="event-pg-symbol-001",
        symbol="ETHUSDT",
        price="2500.10",
        timestamp=base_time + timedelta(seconds=2),
    )

    second = _trade(
        trade_id="trade-pg-symbol-002",
        event_id="event-pg-symbol-002",
        symbol="ETHUSDT",
        price="2501.20",
        timestamp=base_time + timedelta(seconds=1),
    )

    other_symbol = _trade(
        trade_id="trade-pg-symbol-003",
        event_id="event-pg-symbol-003",
        symbol="BTCUSDT",
        timestamp=base_time,
    )

    for trade in (first, second, other_symbol):
        repository.save(trade)

    repository._connection.commit()

    trades = repository.list_by_symbol("ETHUSDT")

    assert trades == (second, first)


def test_repository_lists_trades_by_time_range(repository) -> None:
    """Trades can be queried using an inclusive timestamp range."""

    base_time = datetime(
        2026,
        9,
        14,
        13,
        0,
        tzinfo=timezone.utc,
    )

    before = _trade(
        trade_id="trade-pg-range-001",
        event_id="event-pg-range-001",
        timestamp=base_time - timedelta(seconds=1),
    )

    inside = _trade(
        trade_id="trade-pg-range-002",
        event_id="event-pg-range-002",
        timestamp=base_time,
    )

    after = _trade(
        trade_id="trade-pg-range-003",
        event_id="event-pg-range-003",
        timestamp=base_time + timedelta(seconds=1),
    )

    for trade in (before, inside, after):
        repository.save(trade)

    repository._connection.commit()

    trades = repository.list_by_time_range(
        base_time,
        base_time,
    )

    assert trades == (inside,)


def test_repository_upserts_existing_trade_id(repository) -> None:
    """Saving an existing trade_id updates the stored trade."""

    original = _trade(
        trade_id="trade-pg-upsert-001",
        event_id="event-pg-upsert-001",
        price="100.00",
        quantity=1,
    )

    updated = _trade(
        trade_id="trade-pg-upsert-001",
        event_id="event-pg-upsert-002",
        price="125.50",
        quantity=5,
        taker_side="SELL",
    )

    repository.save(original)
    repository._connection.commit()

    repository.save(updated)
    repository._connection.commit()

    loaded = repository.get_by_id("trade-pg-upsert-001")

    assert loaded == updated



def test_database_enforces_trade_constraints(
    migrated_connection,
) -> None:
    """PostgreSQL enforces the authoritative trade schema constraints."""

    with migrated_connection.cursor() as cursor:
        with pytest.raises(psycopg.errors.CheckViolation):
            cursor.execute(
                """
                INSERT INTO trades (
                    event_id,
                    event_type,
                    trade_id,
                    symbol,
                    price,
                    quantity,
                    timestamp,
                    taker_side,
                    buy_order_id,
                    sell_order_id,
                    taker_order_id,
                    maker_order_id
                )
                VALUES (
                    'event-pg-invalid-001',
                    'TRADE',
                    'trade-pg-invalid-001',
                    'BTCUSDT',
                    0,
                    1,
                    CURRENT_TIMESTAMP,
                    'BUY',
                    'buy-001',
                    'sell-001',
                    'taker-001',
                    'maker-001'
                )
                """
            )

    migrated_connection.rollback()

    with migrated_connection.cursor() as cursor:
        cursor.execute(
            """
            SELECT COUNT(*)
            FROM trades
            WHERE trade_id = 'trade-pg-invalid-001'
            """
        )

        count = cursor.fetchone()[0]

    assert count == 0



def test_failed_migration_is_rolled_back(
    migrated_connection,
    tmp_path: Path,
) -> None:
    """A failed migration does not leave partial schema changes."""

    failed_migration = tmp_path / "002_broken.sql"

    failed_migration.write_text(
        """
        CREATE TABLE should_be_rolled_back (
            id INTEGER PRIMARY KEY
        );

        THIS IS NOT VALID SQL;
        """,
        encoding="utf-8",
    )

    runner = MigrationRunner(
        migrated_connection,
        tmp_path,
    )

    with pytest.raises(psycopg.errors.SyntaxError):
        runner.run()

    migrated_connection.rollback()

    with migrated_connection.cursor() as cursor:
        cursor.execute(
            """
            SELECT to_regclass(
                format(
                    '%I.should_be_rolled_back',
                    current_schema()
                )
            )
            """
        )
        table = cursor.fetchone()[0]

        cursor.execute(
            """
            SELECT version
            FROM schema_migrations
            ORDER BY version
            """
        )
        versions = cursor.fetchall()

    assert table is None
    assert versions == [("001",)]
