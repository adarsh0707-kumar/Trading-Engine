"""PostgreSQL implementation of the trade repository contract."""

from __future__ import annotations

from datetime import datetime

import psycopg

from analytics.models import Trade


class PostgresTradeRepository:
    """Persist authoritative trade events in PostgreSQL.

    The repository receives an existing Psycopg connection so connection
    lifecycle and transaction management remain outside the repository.
    """

    def __init__(self, connection: psycopg.Connection) -> None:
        """Initialize the repository with an existing database connection."""

        if connection is None:
            raise TypeError("connection must not be None")

        self._connection = connection

    def save(self, trade: Trade) -> None:
        """Persist one trade event.

        The trade identifier is unique. Saving the same trade_id again
        replaces the existing row.
        """

        if not isinstance(trade, Trade):
            raise TypeError("trade must be a Trade")

        with self._connection.cursor() as cursor:
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
                    %(event_id)s,
                    %(event_type)s,
                    %(trade_id)s,
                    %(symbol)s,
                    %(price)s,
                    %(quantity)s,
                    %(timestamp)s,
                    %(taker_side)s,
                    %(buy_order_id)s,
                    %(sell_order_id)s,
                    %(taker_order_id)s,
                    %(maker_order_id)s
                )
                ON CONFLICT (trade_id)
                DO UPDATE SET
                    event_id = EXCLUDED.event_id,
                    event_type = EXCLUDED.event_type,
                    symbol = EXCLUDED.symbol,
                    price = EXCLUDED.price,
                    quantity = EXCLUDED.quantity,
                    timestamp = EXCLUDED.timestamp,
                    taker_side = EXCLUDED.taker_side,
                    buy_order_id = EXCLUDED.buy_order_id,
                    sell_order_id = EXCLUDED.sell_order_id,
                    taker_order_id = EXCLUDED.taker_order_id,
                    maker_order_id = EXCLUDED.maker_order_id
                """,
                {
                    "event_id": trade.event_id,
                    "event_type": trade.event_type,
                    "trade_id": trade.trade_id,
                    "symbol": trade.symbol,
                    "price": trade.price,
                    "quantity": trade.quantity,
                    "timestamp": trade.timestamp,
                    "taker_side": trade.taker_side,
                    "buy_order_id": trade.buy_order_id,
                    "sell_order_id": trade.sell_order_id,
                    "taker_order_id": trade.taker_order_id,
                    "maker_order_id": trade.maker_order_id,
                },
            )

    def get_by_id(self, trade_id: str) -> Trade | None:
        """Return a trade by its trade identifier."""

        with self._connection.cursor() as cursor:
            cursor.execute(
                """
                SELECT
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
                FROM trades
                WHERE trade_id = %s
                """,
                (trade_id,),
            )

            row = cursor.fetchone()

        if row is None:
            return None

        return self._row_to_trade(row)

    def list_by_symbol(
        self,
        symbol: str,
    ) -> tuple[Trade, ...]:
        """Return trades for a symbol ordered by timestamp."""

        with self._connection.cursor() as cursor:
            cursor.execute(
                """
                SELECT
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
                FROM trades
                WHERE symbol = %s
                ORDER BY timestamp ASC, trade_id ASC
                """,
                (symbol,),
            )

            rows = cursor.fetchall()

        return tuple(self._row_to_trade(row) for row in rows)

    def list_by_time_range(
        self,
        start: datetime,
        end: datetime,
    ) -> tuple[Trade, ...]:
        """Return trades within an inclusive timestamp range."""

        if start > end:
            raise ValueError("start must not be after end")

        with self._connection.cursor() as cursor:
            cursor.execute(
                """
                SELECT
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
                FROM trades
                WHERE timestamp >= %s
                  AND timestamp <= %s
                ORDER BY timestamp ASC, trade_id ASC
                """,
                (start, end),
            )

            rows = cursor.fetchall()

        return tuple(self._row_to_trade(row) for row in rows)

    @staticmethod
    def _row_to_trade(row: tuple[object, ...]) -> Trade:
        """Convert a PostgreSQL row into a Trade domain object."""

        return Trade(
            event_id=row[0],
            event_type=row[1],
            trade_id=row[2],
            symbol=row[3],
            price=row[4],
            quantity=row[5],
            timestamp=row[6],
            taker_side=row[7],
            buy_order_id=row[8],
            sell_order_id=row[9],
            taker_order_id=row[10],
            maker_order_id=row[11],
        )


__all__ = ["PostgresTradeRepository"]