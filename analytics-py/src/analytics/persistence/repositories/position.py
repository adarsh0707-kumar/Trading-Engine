"""Repository contract for persisted position state."""

from __future__ import annotations

from typing import Protocol

from analytics.risk.risk_manager import RiskSnapshot


class PositionRepository(Protocol):
    """Database-agnostic contract for position-state persistence."""

    def save(
        self,
        symbol: str,
        snapshot: RiskSnapshot,
    ) -> None:
        """Persist the latest position state for a symbol."""
        ...

    def get_by_symbol(
        self,
        symbol: str,
    ) -> RiskSnapshot | None:
        """Return the latest position state for a symbol."""
        ...


__all__ = ["PositionRepository"]