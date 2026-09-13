"""In-memory implementation of the trade repository contract."""

from __future__ import annotations

from datetime import datetime

from analytics.models import Trade


class InMemoryTradeRepository:
    """Store authoritative trade events in memory.

    This implementation is intended for tests, local development, and
    repository-contract validation. It has no database dependencies.
    """

    def __init__(self) -> None:
        """Initialize an empty trade store."""

        self._trades: dict[str, Trade] = {}

    def save(self, trade: Trade) -> None:
        """Persist one trade, replacing an existing trade with the same ID."""

        if not isinstance(trade, Trade):
            raise TypeError("trade must be a Trade")

        self._trades[trade.trade_id] = trade

    def get_by_id(self, trade_id: str) -> Trade | None:
        """Return a trade by its trade identifier."""

        return self._trades.get(trade_id)

    def list_by_symbol(
        self,
        symbol: str,
    ) -> tuple[Trade, ...]:
        """Return trades for a symbol in insertion order."""

        return tuple(
            trade
            for trade in self._trades.values()
            if trade.symbol == symbol
        )

    def list_by_time_range(
        self,
        start: datetime,
        end: datetime,
    ) -> tuple[Trade, ...]:
        """Return trades whose timestamps fall within an inclusive range."""

        if start > end:
            raise ValueError("start must not be after end")

        return tuple(
            trade
            for trade in self._trades.values()
            if start <= trade.timestamp <= end
        )


__all__ = ["InMemoryTradeRepository"]
