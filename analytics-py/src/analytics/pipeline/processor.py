"""Streaming processor for indicators and risk analytics."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import date
from decimal import Decimal
from typing import Dict, List

from analytics.config.risk_limits import RiskLimitConfig
from analytics.indicators import calculate_ema, calculate_sma, calculate_vwap, calculate_volatility
from analytics.models import AnalyticsResult, ProcessedTrade, Trade
from analytics.risk import RiskEventGenerator, RiskLimitEvaluator, RiskManager


@dataclass
class _SymbolState:
    """Mutable per-symbol streaming state."""
    prices: List[Decimal] = field(default_factory=list)
    quantities: List[int] = field(default_factory=list)
    risk_manager: RiskManager | None = None
    risk_limit_evaluator: RiskLimitEvaluator | None = None
    risk_event_generator: RiskEventGenerator | None = None
    risk_day: date | None = None
    day_start_equity: Decimal | None = None


class StreamingProcessor:
    """Consume Trade events and emit analytics and optional risk events."""

    def __init__(
        self,
        *,
        sma_period: int = 5,
        ema_period: int = 5,
        volatility_period: int = 5,
        initial_equity: Decimal = Decimal("10000"),
        risk_limits: RiskLimitConfig | None = None,
    ) -> None:
        if sma_period <= 0:
            raise ValueError("sma_period must be positive")
        if ema_period <= 0:
            raise ValueError("ema_period must be positive")
        if volatility_period <= 0:
            raise ValueError("volatility_period must be positive")
        if initial_equity < 0:
            raise ValueError("initial_equity must not be negative")
        if risk_limits is not None and not isinstance(risk_limits, RiskLimitConfig):
            raise TypeError("risk_limits must be a RiskLimitConfig")
        self._sma_period = sma_period
        self._ema_period = ema_period
        self._volatility_period = volatility_period
        self._initial_equity = initial_equity
        self._risk_limits = risk_limits
        self._symbols: Dict[str, _SymbolState] = {}
        self._sequence = 0

    def process_trade(self, trade: Trade) -> AnalyticsResult:
        """Return analytics only, preserving the original processor API."""
        return self.process_trade_with_risk_events(trade).analytics

    def process_trade_with_risk_events(self, trade: Trade) -> ProcessedTrade:
        """Process one trade and return analytics plus generated risk events."""
        state = self._symbols.setdefault(trade.symbol, _SymbolState())
        if state.risk_manager is None:
            state.risk_manager = RiskManager(initial_equity=self._initial_equity)
        if self._risk_limits is not None:
            if state.risk_limit_evaluator is None:
                state.risk_limit_evaluator = RiskLimitEvaluator(self._risk_limits)
            if state.risk_event_generator is None:
                state.risk_event_generator = RiskEventGenerator(event_prefix=f"risk-{trade.symbol}")

        state.prices.append(trade.price)
        state.quantities.append(trade.quantity)
        vwap = calculate_vwap(state.prices, state.quantities)
        sma = calculate_sma(state.prices, self._sma_period)
        ema = calculate_ema(state.prices, self._ema_period)
        volatility = calculate_volatility(state.prices, self._volatility_period)

        trade_day = trade.timestamp.date()
        if state.risk_day != trade_day:
            state.risk_day = trade_day
            state.day_start_equity = state.risk_manager.snapshot().equity

        risk = state.risk_manager.process_trade(
            quantity=trade.quantity,
            price=trade.price,
            side=trade.taker_side,
        )
        daily_loss = max(Decimal("0"), (state.day_start_equity or Decimal("0")) - risk.equity)

        self._sequence += 1
        analytics = AnalyticsResult(
            event_id=f"analytics-{trade.event_id}-{self._sequence}",
            event_type="ANALYTICS_UPDATE",
            symbol=trade.symbol,
            price=trade.price,
            vwap=vwap,
            sma=sma,
            ema=ema,
            volatility=volatility,
            position=risk.position,
            realized_pnl=risk.realized_pnl,
            unrealized_pnl=risk.unrealized_pnl,
            equity=risk.equity,
            peak_equity=risk.peak_equity,
            drawdown=risk.drawdown,
            timestamp=trade.timestamp,
        )

        risk_events = ()
        if state.risk_limit_evaluator is not None and state.risk_event_generator is not None:
            states = state.risk_limit_evaluator.evaluate(
                snapshot=risk,
                market_price=trade.price,
                daily_loss=daily_loss,
                symbol=trade.symbol,
            )
            risk_events = state.risk_event_generator.generate(
                states=states,
                timestamp=trade.timestamp,
            )

        return ProcessedTrade(
            trade=trade,
            analytics=analytics,
            risk_snapshot=risk,
            risk_events=risk_events,
        )


__all__ = ["StreamingProcessor"]
