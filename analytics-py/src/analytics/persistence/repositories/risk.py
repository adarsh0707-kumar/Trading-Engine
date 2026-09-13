"""Repository contract for persisted risk state and risk events."""

from __future__ import annotations

from datetime import datetime
from typing import Protocol

from analytics.models.risk_event import RiskEvent
from analytics.risk.risk_manager import RiskSnapshot


class RiskRepository(Protocol):
    """Database-agnostic contract for risk-state persistence."""

    def save_risk_state(
        self,
        symbol: str,
        snapshot: RiskSnapshot,
    ) -> None:
        """Persist the latest risk state for a symbol."""
        ...

    def save_event(
        self,
        event: RiskEvent,
    ) -> None:
        """Persist one immutable risk event."""
        ...

    def get_latest_state(
        self,
        symbol: str,
    ) -> RiskSnapshot | None:
        """Return the latest persisted risk state for a symbol."""
        ...

    def list_events(
        self,
        symbol: str,
    ) -> tuple[RiskEvent, ...]:
        """Return persisted risk events for a symbol."""
        ...

    def list_events_by_time_range(
        self,
        symbol: str,
        start: datetime,
        end: datetime,
    ) -> tuple[RiskEvent, ...]:
        """Return risk events within a specified time range."""
        ...


__all__ = ["RiskRepository"]