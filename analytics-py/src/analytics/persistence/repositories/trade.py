"""Repository contract for persisted trade events."""

from __future__ import annotations

from datetime import datetime
from typing import Protocol

from analytics.models import Trade


class TradeRepository(Protocol):
    """Database-agnostic contract for trade persistence."""

    def save(self, trade: Trade) -> None:
        """Persist one authoritative trade event."""
        ...

    def get_by_id(self, trade_id: str) -> Trade | None:
        """Return a trade by its trade identifier."""
        ...

    def list_by_symbol(
        self,
        symbol: str,
    ) -> tuple[Trade, ...]:
        """Return trades for a symbol."""
        ...

    def list_by_time_range(
        self,
        start: datetime,
        end: datetime,
    ) -> tuple[Trade, ...]:
        """Return trades occurring within the specified time range."""
        ...


__all__ = ["TradeRepository"]