"""Unit tests for the streaming analytics processor."""

from __future__ import annotations

from datetime import datetime, timedelta, timezone
from decimal import Decimal

from analytics.models import Trade
from analytics.pipeline import StreamingProcessor

BASE_TIME = datetime(2026, 9, 10, 0, 0, 0, tzinfo=timezone.utc)


def _trade(index: int, price: str, quantity: int = 1, symbol: str = "SIM") -> Trade:
    return Trade(
        event_id=f"evt-{index}",
        event_type="TRADE",
        trade_id=f"trd-{index}",
        symbol=symbol,
        price=Decimal(price),
        quantity=quantity,
        timestamp=BASE_TIME + timedelta(seconds=index),

        taker_side="BUY",
        buy_order_id=f"taker-{index}",
        sell_order_id=f"maker-{index}",
        taker_order_id=f"taker-{index}",
        maker_order_id=f"maker-{index}",

    )


def test_process_trade_emits_analytics_update() -> None:
    processor = StreamingProcessor(sma_period=3, ema_period=3)

    result = processor.process_trade(_trade(1, "100.00"))

    assert result.event_type == "ANALYTICS_UPDATE"
    assert result.symbol == "SIM"
    assert result.price == Decimal("100.00")
    assert result.vwap == Decimal("100.00")
    assert result.sma is None
    assert result.ema is None


def test_indicators_populate_once_period_is_met() -> None:
    processor = StreamingProcessor(sma_period=3, ema_period=3)

    for index, price in enumerate(["100", "101", "102"], start=1):
        result = processor.process_trade(_trade(index, price))

    assert result.sma == Decimal("101")
    assert result.ema is not None
    assert result.vwap == Decimal("101")


def test_symbols_are_tracked_independently() -> None:
    processor = StreamingProcessor(sma_period=2, ema_period=2)

    processor.process_trade(_trade(1, "10", symbol="SIM"))
    processor.process_trade(_trade(2, "500", symbol="OTHER"))
    result = processor.process_trade(_trade(3, "20", symbol="SIM"))

    assert result.symbol == "SIM"
    assert result.sma == Decimal("15")


def test_position_and_pnl_are_calculated_from_trade_side() -> None:
    processor = StreamingProcessor()

    result = processor.process_trade(_trade(1, "100"))

    assert result.position == 1
    assert result.realized_pnl == Decimal("0")
    assert result.unrealized_pnl == Decimal("0")
    assert result.equity == Decimal("10000")
    assert result.peak_equity == Decimal("10000")
    assert result.drawdown == Decimal("0")


def test_event_ids_are_unique_and_deterministic() -> None:
    processor = StreamingProcessor()

    first = processor.process_trade(_trade(1, "100"))
    second = processor.process_trade(_trade(2, "101"))

    assert first.event_id == "analytics-evt-1-1"
    assert second.event_id == "analytics-evt-2-2"


def test_timestamp_is_preserved_from_trade() -> None:
    processor = StreamingProcessor()
    trade = _trade(1, "100")

    result = processor.process_trade(trade)

    assert result.timestamp == trade.timestamp


def test_rejects_non_positive_periods() -> None:
    import pytest

    with pytest.raises(ValueError):
        StreamingProcessor(sma_period=0)

    with pytest.raises(ValueError):
        StreamingProcessor(ema_period=-1)


def test_risk_state_is_propagated_through_processor() -> None:
    processor = StreamingProcessor(initial_equity=Decimal("10000"))

    processor.process_trade(_trade(1, "100"))

    result = processor.process_trade(
        Trade(
            event_id="evt-2",
            event_type="TRADE",
            trade_id="trd-2",
            symbol="SIM",
            price=Decimal("110"),
            quantity=1,
            timestamp=BASE_TIME + timedelta(seconds=2),
            taker_side="SELL",
            buy_order_id="maker-2",
            sell_order_id="taker-2",
            taker_order_id="taker-2",
            maker_order_id="maker-2",
        )
    )

    assert result.position == 0
    assert result.realized_pnl == Decimal("10")
    assert result.unrealized_pnl == Decimal("0")
    assert result.equity == Decimal("10010")
    assert result.peak_equity == Decimal("10010")
    assert result.drawdown == Decimal("0")
