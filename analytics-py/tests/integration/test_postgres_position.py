"""Integration tests for PostgreSQL position persistence."""

from __future__ import annotations

import os
from decimal import Decimal
from pathlib import Path
from uuid import uuid4

import psycopg
import pytest
from psycopg import sql

from analytics.persistence.migrations import MigrationRunner
from analytics.persistence.postgres import PostgresPositionRepository
from analytics.risk.risk_manager import RiskSnapshot


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
    """Return a PostgreSQL position repository."""
    return PostgresPositionRepository(migrated_connection)


def _snapshot(
    *,
    position: int = 10,
    average_entry_price: Decimal | None = Decimal("100.50"),
    realized_pnl: Decimal = Decimal("25.00"),
    unrealized_pnl: Decimal = Decimal("15.00"),
    equity: Decimal = Decimal("1040.00"),
    peak_equity: Decimal = Decimal("1050.00"),
    drawdown: Decimal = Decimal("10.00"),
) -> RiskSnapshot:
    """Build a deterministic risk snapshot."""
    return RiskSnapshot(
        position=position,
        average_entry_price=average_entry_price,
        realized_pnl=realized_pnl,
        unrealized_pnl=unrealized_pnl,
        equity=equity,
        peak_equity=peak_equity,
        drawdown=drawdown,
    )


def test_real_migration_creates_positions_table(
    migrated_connection,
) -> None:
    """The real migration creates the position store."""
    with migrated_connection.cursor() as cursor:
        cursor.execute(
            """
            SELECT column_name
            FROM information_schema.columns
            WHERE table_schema = current_schema()
              AND table_name = 'positions'
            ORDER BY ordinal_position
            """
        )

        columns = [row[0] for row in cursor.fetchall()]

        cursor.execute(
            """
            SELECT indexname
            FROM pg_indexes
            WHERE schemaname = current_schema()
              AND tablename = 'positions'
            ORDER BY indexname
            """
        )

        indexes = {row[0] for row in cursor.fetchall()}

    assert columns == [
        "symbol",
        "position",
        "average_entry_price",
        "realized_pnl",
        "unrealized_pnl",
        "equity",
        "peak_equity",
        "drawdown",
    ]

    assert indexes == {
        "positions_pkey",
    }


def test_save_and_get_round_trip(repository) -> None:
    """A position snapshot survives a PostgreSQL round trip."""
    snapshot = _snapshot()

    repository.save(
        symbol="BTCUSDT",
        snapshot=snapshot,
    )

    repository._connection.commit()

    loaded = repository.get_by_symbol(
        symbol="BTCUSDT",
    )

    assert loaded == snapshot


def test_get_missing_symbol_returns_none(repository) -> None:
    """Missing symbols return no position state."""
    assert repository.get_by_symbol(
        symbol="MISSING_SYMBOL",
    ) is None


def test_save_updates_latest_state_for_symbol(repository) -> None:
    """Saving the same symbol replaces its latest snapshot."""
    first = _snapshot(
        position=10,
        average_entry_price=Decimal("100.00"),
        realized_pnl=Decimal("5.00"),
        unrealized_pnl=Decimal("10.00"),
        equity=Decimal("1015.00"),
        peak_equity=Decimal("1015.00"),
        drawdown=Decimal("0"),
    )

    second = _snapshot(
        position=20,
        average_entry_price=Decimal("102.50"),
        realized_pnl=Decimal("12.00"),
        unrealized_pnl=Decimal("30.00"),
        equity=Decimal("1042.00"),
        peak_equity=Decimal("1042.00"),
        drawdown=Decimal("0"),
    )

    repository.save(
        symbol="BTCUSDT",
        snapshot=first,
    )

    repository._connection.commit()

    repository.save(
        symbol="BTCUSDT",
        snapshot=second,
    )

    repository._connection.commit()

    loaded = repository.get_by_symbol(
        symbol="BTCUSDT",
    )

    assert loaded == second


def test_symbols_are_stored_independently(repository) -> None:
    """Different symbols maintain independent position state."""
    btc = _snapshot(
        position=10,
        average_entry_price=Decimal("100"),
    )

    eth = _snapshot(
        position=-5,
        average_entry_price=Decimal("200"),
    )

    repository.save(
        symbol="BTCUSDT",
        snapshot=btc,
    )

    repository.save(
        symbol="ETHUSDT",
        snapshot=eth,
    )

    repository._connection.commit()

    assert repository.get_by_symbol(
        symbol="BTCUSDT",
    ) == btc

    assert repository.get_by_symbol(
        symbol="ETHUSDT",
    ) == eth


def test_flat_position_allows_null_average_entry_price(
    repository,
) -> None:
    """A flat position has no average entry price."""
    snapshot = _snapshot(
        position=0,
        average_entry_price=None,
    )

    repository.save(
        symbol="BTCUSDT",
        snapshot=snapshot,
    )

    repository._connection.commit()

    loaded = repository.get_by_symbol(
        symbol="BTCUSDT",
    )

    assert loaded == snapshot
    assert loaded is not None
    assert loaded.average_entry_price is None


def test_empty_symbol_is_rejected(repository) -> None:
    """Empty symbols are rejected by the repository."""
    snapshot = _snapshot()

    with pytest.raises(
        ValueError,
        match="symbol must not be empty",
    ):
        repository.save(
            symbol="",
            snapshot=snapshot,
        )

    with pytest.raises(
        ValueError,
        match="symbol must not be empty",
    ):
        repository.get_by_symbol(
            symbol="",
        )


def test_invalid_snapshot_type_is_rejected(repository) -> None:
    """The repository accepts only RiskSnapshot values."""
    with pytest.raises(
        TypeError,
        match="snapshot must be a RiskSnapshot",
    ):
        repository.save(
            symbol="BTCUSDT",
            snapshot=None,
        )


def test_position_table_rejects_nonzero_position_without_entry_price(
    migrated_connection,
) -> None:
    """An open position must have an average entry price."""
    with migrated_connection.cursor() as cursor:
        with pytest.raises(psycopg.errors.CheckViolation):
            cursor.execute(
                """
                INSERT INTO positions (
                    symbol,
                    position,
                    average_entry_price,
                    realized_pnl,
                    unrealized_pnl,
                    equity,
                    peak_equity,
                    drawdown
                )
                VALUES (
                    'INVALID',
                    10,
                    NULL,
                    0,
                    0,
                    1000,
                    1000,
                    0
                )
                """
            )

    migrated_connection.rollback()


def test_position_table_rejects_flat_position_with_entry_price(
    migrated_connection,
) -> None:
    """A flat position must not retain an entry price."""
    with migrated_connection.cursor() as cursor:
        with pytest.raises(psycopg.errors.CheckViolation):
            cursor.execute(
                """
                INSERT INTO positions (
                    symbol,
                    position,
                    average_entry_price,
                    realized_pnl,
                    unrealized_pnl,
                    equity,
                    peak_equity,
                    drawdown
                )
                VALUES (
                    'INVALID',
                    0,
                    100.00,
                    0,
                    0,
                    1000,
                    1000,
                    0
                )
                """
            )

    migrated_connection.rollback()


def test_position_table_rejects_negative_drawdown(
    migrated_connection,
) -> None:
    """Drawdown cannot be negative."""
    with migrated_connection.cursor() as cursor:
        with pytest.raises(psycopg.errors.CheckViolation):
            cursor.execute(
                """
                INSERT INTO positions (
                    symbol,
                    position,
                    average_entry_price,
                    realized_pnl,
                    unrealized_pnl,
                    equity,
                    peak_equity,
                    drawdown
                )
                VALUES (
                    'INVALID',
                    10,
                    100.00,
                    0,
                    0,
                    1000,
                    1000,
                    -1
                )
                """
            )

    migrated_connection.rollback()


def test_position_table_rejects_equity_above_peak(
    migrated_connection,
) -> None:
    """Peak equity must be greater than or equal to equity."""
    with migrated_connection.cursor() as cursor:
        with pytest.raises(psycopg.errors.CheckViolation):
            cursor.execute(
                """
                INSERT INTO positions (
                    symbol,
                    position,
                    average_entry_price,
                    realized_pnl,
                    unrealized_pnl,
                    equity,
                    peak_equity,
                    drawdown
                )
                VALUES (
                    'INVALID',
                    10,
                    100.00,
                    0,
                    0,
                    1100,
                    1000,
                    0
                )
                """
            )

    migrated_connection.rollback()