"""Processed trade result combining analytics and risk state."""

from __future__ import annotations

from dataclasses import dataclass

from analytics.models.analytics_result import AnalyticsResult
from analytics.models.risk_event import RiskEvent
from analytics.models.trade import Trade
from analytics.risk.risk_manager import RiskSnapshot


@dataclass(frozen=True, slots=True)
class ProcessedTrade:
    """Immutable result produced from processing one trade.

    The object carries every domain value required by downstream consumers,
    including persistence, without requiring them to reconstruct state from
    derived analytics values.
    """

    trade: Trade
    analytics: AnalyticsResult
    risk_snapshot: RiskSnapshot
    risk_events: tuple[RiskEvent, ...]

    def __post_init__(self) -> None:
        """Validate the processed trade result."""

        if not isinstance(self.trade, Trade):
            raise TypeError("trade must be a Trade")

        if not isinstance(self.analytics, AnalyticsResult):
            raise TypeError("analytics must be an AnalyticsResult")

        if not isinstance(self.risk_snapshot, RiskSnapshot):
            raise TypeError("risk_snapshot must be a RiskSnapshot")

        if not isinstance(self.risk_events, tuple):
            raise TypeError("risk_events must be a tuple")

        if not all(
            isinstance(event, RiskEvent)
            for event in self.risk_events
        ):
            raise TypeError("risk_events must contain only RiskEvent objects")


__all__ = ["ProcessedTrade"]
