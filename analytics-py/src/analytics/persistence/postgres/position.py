"""PostgreSQL persistence implementation for position state."""

from __future__ import annotations

from decimal import Decimal

import psycopg

from analytics.risk.risk_manager import RiskSnapshot


class PostgresPositionRepository:
    """Persist the latest risk snapshot for each symbol in PostgreSQL."""

    def __init__(self, connection: psycopg.Connection) -> None:
        if connection is None:
            raise TypeError("connection must not be None")

        self._connection = connection

    def save(
        self,
        *,
        symbol: str,
        snapshot: RiskSnapshot,
    ) -> None:
        """Persist the latest position state for a symbol."""
        if not isinstance(symbol, str):
            raise TypeError("symbol must be a string")

        if not symbol:
            raise ValueError("symbol must not be empty")

        if not isinstance(snapshot, RiskSnapshot):
            raise TypeError("snapshot must be a RiskSnapshot")

        with self._connection.cursor() as cursor:
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
                    %(symbol)s,
                    %(position)s,
                    %(average_entry_price)s,
                    %(realized_pnl)s,
                    %(unrealized_pnl)s,
                    %(equity)s,
                    %(peak_equity)s,
                    %(drawdown)s
                )
                ON CONFLICT (symbol) DO UPDATE SET
                    position = EXCLUDED.position,
                    average_entry_price = EXCLUDED.average_entry_price,
                    realized_pnl = EXCLUDED.realized_pnl,
                    unrealized_pnl = EXCLUDED.unrealized_pnl,
                    equity = EXCLUDED.equity,
                    peak_equity = EXCLUDED.peak_equity,
                    drawdown = EXCLUDED.drawdown
                """,
                {
                    "symbol": symbol,
                    "position": snapshot.position,
                    "average_entry_price": snapshot.average_entry_price,
                    "realized_pnl": snapshot.realized_pnl,
                    "unrealized_pnl": snapshot.unrealized_pnl,
                    "equity": snapshot.equity,
                    "peak_equity": snapshot.peak_equity,
                    "drawdown": snapshot.drawdown,
                },
            )

    def get_by_symbol(
        self,
        *,
        symbol: str,
    ) -> RiskSnapshot | None:
        """Return the latest position state for a symbol."""
        if not isinstance(symbol, str):
            raise TypeError("symbol must be a string")

        if not symbol:
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
                FROM positions
                WHERE symbol = %s
                """,
                (symbol,),
            )
            row = cursor.fetchone()

        if row is None:
            return None

        return self._row_to_snapshot(row)

    @staticmethod
    def _row_to_snapshot(
        row: tuple[
            int,
            Decimal | None,
            Decimal,
            Decimal,
            Decimal,
            Decimal,
            Decimal,
        ],
    ) -> RiskSnapshot:
        """Convert a PostgreSQL row into a RiskSnapshot."""
        return RiskSnapshot(
            position=row[0],
            average_entry_price=row[1],
            realized_pnl=row[2],
            unrealized_pnl=row[3],
            equity=row[4],
            peak_equity=row[5],
            drawdown=row[6],
        )


__all__ = ["PostgresPositionRepository"]