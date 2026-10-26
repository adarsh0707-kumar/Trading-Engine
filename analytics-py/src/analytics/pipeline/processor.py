"""Streaming processor for indicators and risk analytics."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import date, datetime
from decimal import Decimal
from typing import Dict, Iterable, List

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
    """Consume Trade events and emit analytics and optional risk events.

    Streaming calls remain idempotent by trade_id. Historical recovery uses
    replay_trades(), which rebuilds every derived result in stable event-time
    order so arrival order cannot affect the recovered analytics state.
    """

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
        self._processed_trades: Dict[str, ProcessedTrade] = {}
        self._sequence = 0
        self._latest_order_key_by_symbol: Dict[str, tuple[datetime, str]] = {}

    def process_trade(self, trade: Trade) -> AnalyticsResult:
        """Return analytics only, preserving the original processor API."""
        return self.process_trade_with_risk_events(trade).analytics

    def has_processed_trade(self, trade_id: str) -> bool:
        """Return whether a trade ID has already been consumed."""
        return trade_id in self._processed_trades

    def is_late_trade(self, trade: Trade) -> bool:
        """Return whether a new trade predates the latest event for its symbol."""
        latest_key = self._latest_order_key_by_symbol.get(trade.symbol)
        return latest_key is not None and (trade.timestamp, trade.trade_id) < latest_key

    def processed_results(self) -> tuple[ProcessedTrade, ...]:
        """Return current results in deterministic chronological order."""
        return tuple(sorted(
            self._processed_trades.values(),
            key=lambda result: (
                result.trade.timestamp,
                result.trade.symbol,
                result.trade.trade_id,
            ),
        ))

    def replay_trades(self, trades: Iterable[Trade]) -> tuple[ProcessedTrade, ...]:
        """Reset derived state and replay unique authoritative trades chronologically.

        Trade IDs are idempotency keys. If the input contains duplicate IDs,
        the first occurrence is retained; all unique trades are ordered by
        timestamp, symbol, and trade_id for deterministic tie-breaking.
        """
        unique: dict[str, Trade] = {}
        for trade in trades:
            if not isinstance(trade, Trade):
                raise TypeError("trades must contain only Trade objects")
            unique.setdefault(trade.trade_id, trade)

        ordered = sorted(
            unique.values(),
            key=lambda trade: (trade.timestamp, trade.symbol, trade.trade_id),
        )
        self._symbols = {}
        self._processed_trades = {}
        self._sequence = 0
        self._latest_order_key_by_symbol = {}
        for trade in ordered:
            self._process_one(trade)
        return self.processed_results()

    def process_trade_with_risk_events(self, trade: Trade) -> ProcessedTrade:
        """Process one trade and return analytics plus generated risk events.

        A trade ID is the engine-assigned idempotency key. Return the original
        result for redelivered live/history events so duplicate delivery cannot
        mutate indicators, risk state, or the analytics sequence twice.
        """
        previous = self._processed_trades.get(trade.trade_id)
        if previous is not None:
            return previous
        return self._process_one(trade)

    def _process_one(self, trade: Trade) -> ProcessedTrade:
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

        result = ProcessedTrade(
            trade=trade,
            analytics=analytics,
            risk_snapshot=risk,
            risk_events=risk_events,
        )
        self._processed_trades[trade.trade_id] = result
        order_key = (trade.timestamp, trade.trade_id)
        latest_key = self._latest_order_key_by_symbol.get(trade.symbol)
        if latest_key is None or order_key > latest_key:
            self._latest_order_key_by_symbol[trade.symbol] = order_key
        return result


__all__ = ["StreamingProcessor"]
