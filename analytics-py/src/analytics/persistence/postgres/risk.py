"""PostgreSQL repository for persisted risk state and risk events."""

from __future__ import annotations

from datetime import datetime
from decimal import Decimal

from analytics.models.risk_event import RiskEvent
from analytics.models.risk_limit import RiskLimitStatus, RiskLimitType
from analytics.risk.risk_manager import RiskSnapshot


class PostgresRiskRepository:
    """Persist risk snapshots and immutable risk events in PostgreSQL."""

    def __init__(self, connection) -> None:
        if connection is None:
            raise TypeError("connection must not be None")

        self._connection = connection

    def save_risk_state(
        self,
        *,
        symbol: str,
        snapshot: RiskSnapshot,
    ) -> None:
        """Persist the latest risk state for a symbol."""

        if not isinstance(symbol, str):
            raise TypeError("symbol must be a string")

        if not symbol.strip():
            raise ValueError("symbol must not be empty")

        if not isinstance(snapshot, RiskSnapshot):
            raise TypeError("snapshot must be a RiskSnapshot")

        with self._connection.cursor() as cursor:
            cursor.execute(
                """
                INSERT INTO risk_state (
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
                    %s, %s, %s, %s, %s, %s, %s, %s
                )
                ON CONFLICT (symbol)
                DO UPDATE SET
                    position = EXCLUDED.position,
                    average_entry_price = EXCLUDED.average_entry_price,
                    realized_pnl = EXCLUDED.realized_pnl,
                    unrealized_pnl = EXCLUDED.unrealized_pnl,
                    equity = EXCLUDED.equity,
                    peak_equity = EXCLUDED.peak_equity,
                    drawdown = EXCLUDED.drawdown
                """,
                (
                    symbol,
                    snapshot.position,
                    snapshot.average_entry_price,
                    snapshot.realized_pnl,
                    snapshot.unrealized_pnl,
                    snapshot.equity,
                    snapshot.peak_equity,
                    snapshot.drawdown,
                ),
            )

    def save_event(
        self,
        *,
        event: RiskEvent,
    ) -> None:
        """Persist one immutable risk event."""

        if not isinstance(event, RiskEvent):
            raise TypeError("event must be a RiskEvent")

        with self._connection.cursor() as cursor:
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
                    %s, %s, %s, %s, %s, %s, %s, %s, %s
                )
                ON CONFLICT (event_id) DO NOTHING
                """,
                (
                    event.event_id,
                    event.event_type,
                    event.symbol,
                    event.limit_type.value,
                    event.status.value,
                    event.threshold,
                    event.warning_threshold,
                    event.current_value,
                    event.timestamp,
                ),
            )

    def get_latest_state(
        self,
        *,
        symbol: str,
    ) -> RiskSnapshot | None:
        """Return the latest persisted risk state for a symbol."""

        if not isinstance(symbol, str):
            raise TypeError("symbol must be a string")

        if not symbol.strip():
            raise ValueError("symbol must not be empty")

        with self._connection.cursor() as cursor:
            cursor.execute(
                """
                SELECT
                    position,
                    average_entry_price,
                    realized_pnl,
                    unrealized_pnl,
                    equity,
                    peak_equity,
                    drawdown
                FROM risk_state
                WHERE symbol = %s
                """,
                (symbol,),
            )
            row = cursor.fetchone()

        if row is None:
            return None

        return self._row_to_snapshot(row)

    def list_events(
        self,
        *,
        symbol: str,
    ) -> tuple[RiskEvent, ...]:
        """Return persisted risk events for a symbol."""

        if not isinstance(symbol, str):
            raise TypeError("symbol must be a string")

        if not symbol.strip():
            raise ValueError("symbol must not be empty")

        with self._connection.cursor() as cursor:
            cursor.execute(
                """
                SELECT
                    event_id,
                    event_type,
                    symbol,
                    limit_type,
                    status,
                    threshold,
                    warning_threshold,
                    current_value,
                    timestamp
                FROM risk_events
                WHERE symbol = %s
                ORDER BY timestamp ASC, event_id ASC
                """,
                (symbol,),
            )
            rows = cursor.fetchall()

        return tuple(self._row_to_event(row) for row in rows)

    def list_events_by_time_range(
        self,
        *,
        symbol: str,
        start: datetime,
        end: datetime,
    ) -> tuple[RiskEvent, ...]:
        """Return risk events within a specified time range."""

        if not isinstance(symbol, str):
            raise TypeError("symbol must be a string")

        if not symbol.strip():
            raise ValueError("symbol must not be empty")

        if not isinstance(start, datetime):
            raise TypeError("start must be a datetime")

        if not isinstance(end, datetime):
            raise TypeError("end must be a datetime")

        if start >= end:
            raise ValueError("start must be before end")

        with self._connection.cursor() as cursor:
            cursor.execute(
                """
                SELECT
                    event_id,
                    event_type,
                    symbol,
                    limit_type,
                    status,
                    threshold,
                    warning_threshold,
                    current_value,
                    timestamp
                FROM risk_events
                WHERE symbol = %s
                  AND timestamp >= %s
                  AND timestamp < %s
                ORDER BY timestamp ASC, event_id ASC
                """,
                (symbol, start, end),
            )
            rows = cursor.fetchall()

        return tuple(self._row_to_event(row) for row in rows)

    @staticmethod
    def _row_to_snapshot(row: tuple) -> RiskSnapshot:
        """Convert a database row into a RiskSnapshot."""

        return RiskSnapshot(
            position=int(row[0]),
            average_entry_price=(
                Decimal(row[1]) if row[1] is not None else None
            ),
            realized_pnl=Decimal(row[2]),
            unrealized_pnl=Decimal(row[3]),
            equity=Decimal(row[4]),
            peak_equity=Decimal(row[5]),
            drawdown=Decimal(row[6]),
        )

    @staticmethod
    def _row_to_event(row: tuple) -> RiskEvent:
        """Convert a database row into a RiskEvent."""

        return RiskEvent(
            event_id=row[0],
            event_type=row[1],
            symbol=row[2],
            limit_type=RiskLimitType(row[3]),
            status=RiskLimitStatus(row[4]),
            threshold=Decimal(row[5]),
            warning_threshold=Decimal(row[6]),
            current_value=Decimal(row[7]),
            timestamp=row[8],
        )


__all__ = ["PostgresRiskRepository"]