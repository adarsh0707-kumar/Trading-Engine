"""Streaming processor that turns Trade events into AnalyticsResult snapshots.

Position, PnL, drawdown, and equity are reported as zero placeholders in
Phase 3.5. The TRADE message now carries ``taker_side``, so the direction
of each fill is available; consuming it to maintain position and PnL is
Phase 3.6 work.

Volatility is intentionally not calculated here: AnalyticsResult has no
volatility field yet, so there is nowhere to put it.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from decimal import Decimal
from typing import Dict, List

from analytics.indicators import calculate_ema, calculate_sma, calculate_vwap
from analytics.models import AnalyticsResult, Trade


@dataclass
class _SymbolState:
    """Mutable per-symbol streaming state."""

    prices: List[Decimal] = field(default_factory=list)
    quantities: List[int] = field(default_factory=list)


class StreamingProcessor:
    """Consume Trade events and emit deterministic AnalyticsResult snapshots."""

    def __init__(
        self,
        *,
        sma_period: int = 5,
        ema_period: int = 5,
    ) -> None:
        if sma_period <= 0:
            raise ValueError("sma_period must be positive")
        if ema_period <= 0:
            raise ValueError("ema_period must be positive")

        self._sma_period = sma_period
        self._ema_period = ema_period
        self._symbols: Dict[str, _SymbolState] = {}
        self._sequence = 0

    def process_trade(self, trade: Trade) -> AnalyticsResult:
        """Update per-symbol indicator state and return an AnalyticsResult."""
        state = self._symbols.setdefault(trade.symbol, _SymbolState())
        state.prices.append(trade.price)
        state.quantities.append(trade.quantity)

        vwap = calculate_vwap(state.prices, state.quantities)
        sma = calculate_sma(state.prices, self._sma_period)
        ema = calculate_ema(state.prices, self._ema_period)

        self._sequence += 1

        return AnalyticsResult(
            event_id=f"analytics-{trade.event_id}-{self._sequence}",
            event_type="ANALYTICS_UPDATE",
            symbol=trade.symbol,
            price=trade.price,
            vwap=vwap,
            sma=sma,
            ema=ema,
            position=0,
            realized_pnl=Decimal("0"),
            unrealized_pnl=Decimal("0"),
            equity=Decimal("0"),
            peak_equity=Decimal("0"),
            drawdown=Decimal("0"),
            timestamp=trade.timestamp,
        )


__all__ = ["StreamingProcessor"]
