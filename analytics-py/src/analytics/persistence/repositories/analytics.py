"""Repository contract for persisted analytics results."""

from __future__ import annotations

from datetime import datetime
from typing import Protocol

from analytics.models import AnalyticsResult


class AnalyticsRepository(Protocol):
    """Database-agnostic contract for analytics-result persistence."""

    def save(self, result: AnalyticsResult) -> None:
        """Persist one analytics result."""
        ...

    def get_by_event_id(
        self,
        event_id: str,
    ) -> AnalyticsResult | None:
        """Return an analytics result by event identifier."""
        ...

    def list_by_symbol(
        self,
        symbol: str,
    ) -> tuple[AnalyticsResult, ...]:
        """Return analytics results for a symbol."""
        ...

    def list_by_time_range(
        self,
        start: datetime,
        end: datetime,
    ) -> tuple[AnalyticsResult, ...]:
        """Return analytics results within the specified time range."""
        ...


__all__ = ["AnalyticsRepository"]