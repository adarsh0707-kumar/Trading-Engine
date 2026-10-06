"""PostgreSQL implementation of the analytics repository contract."""

from __future__ import annotations

from datetime import datetime

import psycopg

from analytics.models import AnalyticsResult


class PostgresAnalyticsRepository:
    """Persist derived analytics results in PostgreSQL.

    The repository receives an existing Psycopg connection so connection
    lifecycle and transaction management remain outside the repository.
    """

    def __init__(self, connection: psycopg.Connection) -> None:
        """Initialize the repository with an existing database connection."""

        if connection is None:
            raise TypeError("connection must not be None")

        self._connection = connection

    def save(self, result: AnalyticsResult) -> None:
        """Persist one analytics result.

        event_id is the stable identifier for an analytics update.
        Saving the same event_id again replaces the existing derived result.
        """

        if not isinstance(result, AnalyticsResult):
            raise TypeError("result must be an AnalyticsResult")

        with self._connection.cursor() as cursor:
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
                    volatility,
                    position,
                    realized_pnl,
                    unrealized_pnl,
                    equity,
                    peak_equity,
                    drawdown,
                    timestamp
                )
                VALUES (
                    %(event_id)s,
                    %(event_type)s,
                    %(symbol)s,
                    %(price)s,
                    %(vwap)s,
                    %(sma)s,
                    %(ema)s,
                    %(volatility)s,
                    %(position)s,
                    %(realized_pnl)s,
                    %(unrealized_pnl)s,
                    %(equity)s,
                    %(peak_equity)s,
                    %(drawdown)s,
                    %(timestamp)s
                )
                ON CONFLICT (event_id)
                DO UPDATE SET
                    event_type = EXCLUDED.event_type,
                    symbol = EXCLUDED.symbol,
                    price = EXCLUDED.price,
                    vwap = EXCLUDED.vwap,
                    sma = EXCLUDED.sma,
                    ema = EXCLUDED.ema,
                    volatility = EXCLUDED.volatility,
                    position = EXCLUDED.position,
                    realized_pnl = EXCLUDED.realized_pnl,
                    unrealized_pnl = EXCLUDED.unrealized_pnl,
                    equity = EXCLUDED.equity,
                    peak_equity = EXCLUDED.peak_equity,
                    drawdown = EXCLUDED.drawdown,
                    timestamp = EXCLUDED.timestamp
                """,
                {
                    "event_id": result.event_id,
                    "event_type": result.event_type,
                    "symbol": result.symbol,
                    "price": result.price,
                    "vwap": result.vwap,
                    "sma": result.sma,
                    "ema": result.ema,
                    "volatility": result.volatility,
                    "position": result.position,
                    "realized_pnl": result.realized_pnl,
                    "unrealized_pnl": result.unrealized_pnl,
                    "equity": result.equity,
                    "peak_equity": result.peak_equity,
                    "drawdown": result.drawdown,
                    "timestamp": result.timestamp,
                },
            )

    def get_by_event_id(
        self,
        event_id: str,
    ) -> AnalyticsResult | None:
        """Return an analytics result by event identifier."""

        with self._connection.cursor() as cursor:
            cursor.execute(
                """
                SELECT
                    event_id,
                    event_type,
                    symbol,
                    price,
                    vwap,
                    sma,
                    ema,
                    volatility,
                    position,
                    realized_pnl,
                    unrealized_pnl,
                    equity,
                    peak_equity,
                    drawdown,
                    timestamp
                FROM analytics_results
                WHERE event_id = %s
                """,
                (event_id,),
            )

            row = cursor.fetchone()

        if row is None:
            return None

        return self._row_to_result(row)

    def list_by_symbol(
        self,
        symbol: str,
    ) -> tuple[AnalyticsResult, ...]:
        """Return analytics results for a symbol ordered by timestamp."""

        with self._connection.cursor() as cursor:
            cursor.execute(
                """
                SELECT
                    event_id,
                    event_type,
                    symbol,
                    price,
                    vwap,
                    sma,
                    ema,
                    volatility,
                    position,
                    realized_pnl,
                    unrealized_pnl,
                    equity,
                    peak_equity,
                    drawdown,
                    timestamp
                FROM analytics_results
                WHERE symbol = %s
                ORDER BY timestamp ASC, event_id ASC
                """,
                (symbol,),
            )

            rows = cursor.fetchall()

        return tuple(self._row_to_result(row) for row in rows)

    def list_by_time_range(
        self,
        start: datetime,
        end: datetime,
    ) -> tuple[AnalyticsResult, ...]:
        """Return analytics results within an inclusive timestamp range."""

        if start > end:
            raise ValueError("start must not be after end")

        with self._connection.cursor() as cursor:
            cursor.execute(
                """
                SELECT
                    event_id,
                    event_type,
                    symbol,
                    price,
                    vwap,
                    sma,
                    ema,
                    volatility,
                    position,
                    realized_pnl,
                    unrealized_pnl,
                    equity,
                    peak_equity,
                    drawdown,
                    timestamp
                FROM analytics_results
                WHERE timestamp >= %s
                  AND timestamp <= %s
                ORDER BY timestamp ASC, event_id ASC
                """,
                (start, end),
            )

            rows = cursor.fetchall()

        return tuple(self._row_to_result(row) for row in rows)

    @staticmethod
    def _row_to_result(
        row: tuple[object, ...],
    ) -> AnalyticsResult:
        """Convert a PostgreSQL row into an AnalyticsResult."""

        return AnalyticsResult(
            event_id=row[0],
            event_type=row[1],
            symbol=row[2],
            price=row[3],
            vwap=row[4],
            sma=row[5],
            ema=row[6],
            volatility=row[7],
            position=row[8],
            realized_pnl=row[9],
            unrealized_pnl=row[10],
            equity=row[11],
            peak_equity=row[12],
            drawdown=row[13],
            timestamp=row[14],
        )


__all__ = ["PostgresAnalyticsRepository"]
