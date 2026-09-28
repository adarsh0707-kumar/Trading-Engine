"""Integration tests for PostgreSQL risk persistence."""

from __future__ import annotations

import os
from datetime import datetime, timedelta, timezone
from decimal import Decimal
from pathlib import Path
from uuid import uuid4

import psycopg
import pytest
from psycopg import sql

from analytics.models.risk_event import RiskEvent, RiskEventType
from analytics.models.risk_limit import RiskLimitStatus, RiskLimitType
from analytics.persistence.postgres.risk import PostgresRiskRepository
from analytics.persistence.migrations.runner import MigrationRunner
from analytics.risk.risk_manager import RiskSnapshot


MIGRATIONS_PATH = Path(__file__).resolve().parents[2] / "migrations"


def _database_url() -> str:
    """Return the integration-test database URL."""

    return os.environ.get(
        "TRADING_ENGINE_TEST_DATABASE_URL",
        "postgresql://trading_engine:trading_engine"
        "@127.0.0.1:5432/trading_engine_test",
    )


@pytest.fixture(scope="module")
def postgres_connection():
    """Provide an isolated PostgreSQL schema for the test module."""

    connection = psycopg.connect(_database_url())

    schema_name = f"test_{uuid4().hex}"

    with connection.cursor() as cursor:
        cursor.execute(
            sql.SQL("CREATE SCHEMA {}").format(
                sql.Identifier(schema_name)
            )
        )
        cursor.execute(
            "SELECT pg_catalog.set_config(%s, %s, false)",
            ("search_path", schema_name),
        )

    connection.commit()

    try:
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
def migrated_connection(postgres_connection):
    """Run all migrations inside the isolated test schema."""

    runner = MigrationRunner(
        postgres_connection,
        MIGRATIONS_PATH,
    )

    runner.run()
    postgres_connection.commit()

    return postgres_connection


@pytest.fixture
def repository(migrated_connection):
    """Create a clean PostgreSQL risk repository for each test."""
    with migrated_connection.cursor() as cursor:
        cursor.execute("TRUNCATE risk_events, risk_state")

    migrated_connection.commit()

    return PostgresRiskRepository(migrated_connection)


def _snapshot(
    *,
    position: int = 2,
    average_entry_price: str | None = "100.50",
    realized_pnl: str = "25.25",
    unrealized_pnl: str = "10.75",
    equity: str = "1036",
    peak_equity: str = "1050",
    drawdown: str = "14",
) -> RiskSnapshot:
    """Create a representative risk snapshot."""

    return RiskSnapshot(
        position=position,
        average_entry_price=(
            Decimal(average_entry_price)
            if average_entry_price is not None
            else None
        ),
        realized_pnl=Decimal(realized_pnl),
        unrealized_pnl=Decimal(unrealized_pnl),
        equity=Decimal(equity),
        peak_equity=Decimal(peak_equity),
        drawdown=Decimal(drawdown),
    )


def _event(
    *,
    event_id: str = "risk-max_position-1",
    event_type: str = RiskEventType.LIMIT_WARNING,
    symbol: str | None = "BTC",
    status: RiskLimitStatus = RiskLimitStatus.WARNING,
    current_value: str = "80",
    timestamp: datetime = datetime(
        2026,
        9,
        13,
        12,
        0,
        tzinfo=timezone.utc,
    ),
) -> RiskEvent:
    """Create a representative risk event."""

    return RiskEvent(
        event_id=event_id,
        event_type=event_type,
        symbol=symbol,
        limit_type=RiskLimitType.MAX_POSITION,
        status=status,
        threshold=Decimal("100"),
        warning_threshold=Decimal("80"),
        current_value=Decimal(current_value),
        timestamp=timestamp,
    )


def test_migrations_create_risk_tables(migrated_connection) -> None:
    """Risk migrations create both persistence tables."""

    with migrated_connection.cursor() as cursor:
        cursor.execute(
            """
            SELECT table_name
            FROM information_schema.tables
            WHERE table_schema = current_schema()
              AND table_name IN ('risk_state', 'risk_events')
            ORDER BY table_name
            """
        )

        assert cursor.fetchall() == [
            ("risk_events",),
            ("risk_state",),
        ]


def test_save_and_get_risk_state_round_trip(repository) -> None:
    """Risk snapshots round-trip through PostgreSQL."""

    snapshot = _snapshot()

    repository.save_risk_state(
        symbol="BTC",
        snapshot=snapshot,
    )
    repository._connection.commit()

    result = repository.get_latest_state(symbol="BTC")

    assert result == snapshot


def test_get_missing_risk_state_returns_none(repository) -> None:
    """Missing risk state returns None."""

    assert repository.get_latest_state(
        symbol="MISSING_SYMBOL",
    ) is None


def test_save_risk_state_updates_latest_state(repository) -> None:
    """Saving the same symbol replaces its latest risk state."""

    first = _snapshot(
        position=1,
        average_entry_price="100",
        equity="1010",
        peak_equity="1010",
        drawdown="0",
    )
    second = _snapshot(
        position=3,
        average_entry_price="105",
        equity="1040",
        peak_equity="1060",
        drawdown="20",
    )

    repository.save_risk_state(
        symbol="BTC",
        snapshot=first,
    )
    repository.save_risk_state(
        symbol="BTC",
        snapshot=second,
    )
    repository._connection.commit()

    assert repository.get_latest_state(symbol="BTC") == second


def test_risk_state_isolated_by_symbol(repository) -> None:
    """Risk state for different symbols is stored independently."""

    btc = _snapshot(position=2)
    eth = _snapshot(
        position=-3,
        average_entry_price="2500",
        realized_pnl="-20",
        unrealized_pnl="15",
        equity="995",
        peak_equity="1010",
        drawdown="15",
    )

    repository.save_risk_state(symbol="BTC", snapshot=btc)
    repository.save_risk_state(symbol="ETH", snapshot=eth)
    repository._connection.commit()

    assert repository.get_latest_state(symbol="BTC") == btc
    assert repository.get_latest_state(symbol="ETH") == eth


def test_flat_risk_state_round_trips_null_average_entry_price(
    repository,
) -> None:
    """Flat positions persist a NULL average entry price."""

    snapshot = _snapshot(
        position=0,
        average_entry_price=None,
    )

    repository.save_risk_state(
        symbol="BTC",
        snapshot=snapshot,
    )
    repository._connection.commit()

    assert repository.get_latest_state(symbol="BTC") == snapshot


@pytest.mark.parametrize(
    ("symbol", "expected_exception", "message"),
    [
        ("", ValueError, "symbol must not be empty"),
        ("   ", ValueError, "symbol must not be empty"),
        (123, TypeError, "symbol must be a string"),
    ],
)
def test_risk_state_rejects_invalid_symbol(
    repository,
    symbol,
    expected_exception,
    message,
) -> None:
    """Risk-state persistence rejects invalid symbols."""

    with pytest.raises(expected_exception, match=message):
        repository.save_risk_state(
            symbol=symbol,
            snapshot=_snapshot(),
        )


def test_risk_state_rejects_invalid_snapshot(repository) -> None:
    """Risk-state persistence rejects invalid snapshot types."""

    with pytest.raises(
        TypeError,
        match="snapshot must be a RiskSnapshot",
    ):
        repository.save_risk_state(
            symbol="BTC",
            snapshot=object(),
        )


def test_save_and_list_event_round_trip(repository) -> None:
    """Risk events round-trip through PostgreSQL."""

    event = _event()

    repository.save_event(event=event)
    repository._connection.commit()

    assert repository.list_events(symbol="BTC") == (event,)


def test_breached_event_round_trip(repository) -> None:
    """Breached risk events round-trip correctly."""

    event = _event(
        event_id="risk-max_position-2",
        event_type=RiskEventType.LIMIT_BREACHED,
        status=RiskLimitStatus.BREACHED,
        current_value="100",
    )

    repository.save_event(event=event)
    repository._connection.commit()

    assert repository.list_events(symbol="BTC") == (event,)


def test_event_with_null_symbol_round_trips(repository) -> None:
    """Events with no symbol preserve the NULL symbol."""

    event = _event(
        event_id="risk-max_position-global-1",
        symbol=None,
    )

    repository.save_event(event=event)
    repository._connection.commit()

    with repository._connection.cursor() as cursor:
        cursor.execute(
            """
            SELECT symbol
            FROM risk_events
            WHERE event_id = %s
            """,
            (event.event_id,),
        )

        assert cursor.fetchone() == (None,)


def test_duplicate_event_id_does_not_overwrite_existing_event(
    repository,
) -> None:
    """Risk events remain immutable when the event ID already exists."""

    original = _event(
        current_value="80",
    )
    duplicate = _event(
        current_value="90",
    )

    repository.save_event(event=original)
    repository.save_event(event=duplicate)
    repository._connection.commit()

    assert repository.list_events(symbol="BTC") == (original,)


def test_list_events_orders_by_timestamp_and_event_id(repository) -> None:
    """Events are returned in deterministic chronological order."""

    timestamp = datetime(
        2026,
        9,
        13,
        12,
        0,
        tzinfo=timezone.utc,
    )

    later = _event(
        event_id="risk-max_position-2",
        timestamp=timestamp + timedelta(minutes=2),
    )
    same_time_b = _event(
        event_id="risk-max_position-3",
        timestamp=timestamp,
    )
    same_time_a = _event(
        event_id="risk-max_position-1",
        timestamp=timestamp,
    )

    repository.save_event(event=later)
    repository.save_event(event=same_time_b)
    repository.save_event(event=same_time_a)
    repository._connection.commit()

    assert repository.list_events(symbol="BTC") == (
        same_time_a,
        same_time_b,
        later,
    )


def test_list_events_by_time_range(repository) -> None:
    """Time-range queries return only events in the requested interval."""

    start = datetime(
        2026,
        9,
        13,
        12,
        0,
        tzinfo=timezone.utc,
    )
    middle = start + timedelta(hours=1)
    end = start + timedelta(hours=2)

    before = _event(
        event_id="risk-max_position-before",
        timestamp=start - timedelta(seconds=1),
    )
    included = _event(
        event_id="risk-max_position-included",
        timestamp=middle,
    )
    after = _event(
        event_id="risk-max_position-after",
        timestamp=end,
    )

    repository.save_event(event=before)
    repository.save_event(event=included)
    repository.save_event(event=after)
    repository._connection.commit()

    assert repository.list_events_by_time_range(
        symbol="BTC",
        start=start,
        end=end,
    ) == (included,)


def test_time_range_is_start_inclusive_and_end_exclusive(repository) -> None:
    """Time ranges include start and exclude end."""

    start = datetime(
        2026,
        9,
        13,
        12,
        0,
        tzinfo=timezone.utc,
    )
    end = start + timedelta(hours=1)

    at_start = _event(
        event_id="risk-start",
        timestamp=start,
    )
    at_end = _event(
        event_id="risk-end",
        timestamp=end,
    )

    repository.save_event(event=at_start)
    repository.save_event(event=at_end)
    repository._connection.commit()

    assert repository.list_events_by_time_range(
        symbol="BTC",
        start=start,
        end=end,
    ) == (at_start,)


@pytest.mark.parametrize(
    ("symbol", "expected_exception", "message"),
    [
        ("", ValueError, "symbol must not be empty"),
        ("   ", ValueError, "symbol must not be empty"),
        (123, TypeError, "symbol must be a string"),
    ],
)
def test_list_events_rejects_invalid_symbol(
    repository,
    symbol,
    expected_exception,
    message,
) -> None:
    """Event listing rejects invalid symbols."""

    with pytest.raises(expected_exception, match=message):
        repository.list_events(symbol=symbol)


def test_time_range_rejects_invalid_datetimes(repository) -> None:
    """Time-range queries validate their datetime arguments."""

    with pytest.raises(TypeError, match="start must be a datetime"):
        repository.list_events_by_time_range(
            symbol="BTC",
            start="2026-09-13",
            end=datetime.now(timezone.utc),
        )

    with pytest.raises(TypeError, match="end must be a datetime"):
        repository.list_events_by_time_range(
            symbol="BTC",
            start=datetime.now(timezone.utc),
            end="2026-09-14",
        )


def test_time_range_rejects_reversed_range(repository) -> None:
    """Time-range queries reject reversed ranges."""

    start = datetime(
        2026,
        9,
        14,
        12,
        0,
        tzinfo=timezone.utc,
    )
    end = start - timedelta(hours=1)

    with pytest.raises(
        ValueError,
        match="start must be before end",
    ):
        repository.list_events_by_time_range(
            symbol="BTC",
            start=start,
            end=end,
        )


def test_risk_event_database_constraints(repository) -> None:
    """Database constraints reject invalid risk-event data."""

    with pytest.raises(psycopg.errors.CheckViolation):
        with repository._connection.cursor() as cursor:
            cursor.execute(
                """
                INSERT INTO risk_events (
                    event_id,
                    event_type,
                    symbol,
                    limit_type,
                    status,
                    threshold,
                    warning_threshold,
                    current_value,
                    timestamp
                )
                VALUES (
                    'invalid-threshold',
                    'RISK_LIMIT_WARNING',
                    'BTC',
                    'max_position',
                    'warning',
                    100,
                    100,
                    80,
                    %s
                )
                """,
                (datetime.now(timezone.utc),),
            )

        repository._connection.rollback()