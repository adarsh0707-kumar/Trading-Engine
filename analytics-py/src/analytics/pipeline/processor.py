"""Streaming processor for indicators and risk analytics."""

from __future__ import annotations

from dataclasses import dataclass, field
from decimal import Decimal
from typing import Dict, List

from analytics.indicators import calculate_ema, calculate_sma, calculate_vwap
from analytics.models import AnalyticsResult, Trade
from analytics.risk import RiskManager


@dataclass
class _SymbolState:
    """Mutable per-symbol streaming state."""

    prices: List[Decimal] = field(default_factory=list)
    quantities: List[int] = field(default_factory=list)
    risk_manager: RiskManager | None = None


class StreamingProcessor:
    """Consume Trade events and emit deterministic AnalyticsResult snapshots.

    Indicator and risk state are maintained independently for each symbol.
    """

    def __init__(
        self,
        *,
        sma_period: int = 5,
        ema_period: int = 5,
        initial_equity: Decimal = Decimal("10000"),
    ) -> None:
        if sma_period <= 0:
            raise ValueError("sma_period must be positive")
        if ema_period <= 0:
            raise ValueError("ema_period must be positive")
        if initial_equity < 0:
            raise ValueError("initial_equity must not be negative")

        self._sma_period = sma_period
        self._ema_period = ema_period
        self._initial_equity = initial_equity
        self._symbols: Dict[str, _SymbolState] = {}
        self._sequence = 0

    def process_trade(self, trade: Trade) -> AnalyticsResult:
        """Update indicators and risk state for one trade."""

        state = self._symbols.setdefault(trade.symbol, _SymbolState())

        if state.risk_manager is None:
            state.risk_manager = RiskManager(
                initial_equity=self._initial_equity,
            )

        state.prices.append(trade.price)
        state.quantities.append(trade.quantity)

        vwap = calculate_vwap(state.prices, state.quantities)
        sma = calculate_sma(state.prices, self._sma_period)
        ema = calculate_ema(state.prices, self._ema_period)

        risk = state.risk_manager.process_trade(
            quantity=trade.quantity,
            price=trade.price,
            side=trade.taker_side,
        )

        self._sequence += 1

        return AnalyticsResult(
            event_id=f"analytics-{trade.event_id}-{self._sequence}",
            event_type="ANALYTICS_UPDATE",
            symbol=trade.symbol,
            price=trade.price,
            vwap=vwap,
            sma=sma,
            ema=ema,
            position=risk.position,
            realized_pnl=risk.realized_pnl,
            unrealized_pnl=risk.unrealized_pnl,
            equity=risk.equity,
            peak_equity=risk.peak_equity,
            drawdown=risk.drawdown,
            timestamp=trade.timestamp,
        )


__all__ = ["StreamingProcessor"]
