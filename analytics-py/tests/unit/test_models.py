"""Unit tests for analytics domain models."""

from datetime import datetime, timezone
from decimal import Decimal

import pytest

from analytics.models import AnalyticsResult, Tick, Trade


TIMESTAMP = datetime(2026, 9, 7, 12, 0, 0, tzinfo=timezone.utc)


def test_tick_creation() -> None:
    tick = Tick(
        event_id="evt-000200",
        event_type="MARKET_TICK",
        symbol="SIM",
        price=Decimal("101.20"),
        quantity=15,
        timestamp=TIMESTAMP,
    )

    assert tick.event_id == "evt-000200"
    assert tick.symbol == "SIM"
    assert tick.price == Decimal("101.20")
    assert tick.quantity == 15


def test_tick_to_dict() -> None:
    tick = Tick(
        event_id="evt-000200",
        event_type="MARKET_TICK",
        symbol="SIM",
        price=Decimal("101.20"),
        quantity=15,
        timestamp=TIMESTAMP,
    )

    data = tick.to_dict()

    assert data["event_type"] == "MARKET_TICK"
    assert data["price"] == "101.20"
    assert data["quantity"] == 15
    assert data["timestamp"] == "2026-09-07T12:00:00+00:00"


@pytest.mark.parametrize(
    ("field", "value"),
    [
        ("event_id", ""),
        ("event_type", "TRADE"),
        ("symbol", ""),
        ("price", Decimal("0")),
        ("quantity", 0),
    ],
)
def test_tick_rejects_invalid_values(field: str, value: object) -> None:
    values = {
        "event_id": "evt-000200",
        "event_type": "MARKET_TICK",
        "symbol": "SIM",
        "price": Decimal("101.20"),
        "quantity": 15,
        "timestamp": TIMESTAMP,
    }

    values[field] = value

    with pytest.raises(ValueError):
        Tick(**values)


def test_trade_creation() -> None:
    trade = Trade(
        event_id="evt-000123",
        event_type="TRADE",
        trade_id="trd-000045",
        symbol="SIM",
        price=Decimal("101.25"),
        quantity=40,
        buy_order_id="ord-000010",
        sell_order_id="ord-000009",
        timestamp=TIMESTAMP,
    )

    assert trade.trade_id == "trd-000045"
    assert trade.price == Decimal("101.25")
    assert trade.quantity == 40
    assert trade.buy_order_id == "ord-000010"
    assert trade.sell_order_id == "ord-000009"


def test_trade_to_dict() -> None:
    trade = Trade(
        event_id="evt-000123",
        event_type="TRADE",
        trade_id="trd-000045",
        symbol="SIM",
        price=Decimal("101.25"),
        quantity=40,
        timestamp=TIMESTAMP,
    )

    data = trade.to_dict()

    assert data["event_type"] == "TRADE"
    assert data["trade_id"] == "trd-000045"
    assert data["price"] == "101.25"
    assert data["quantity"] == 40
    assert data["timestamp"] == "2026-09-07T12:00:00+00:00"


@pytest.mark.parametrize(
    ("field", "value"),
    [
        ("event_id", ""),
        ("event_type", "MARKET_TICK"),
        ("trade_id", ""),
        ("symbol", ""),
        ("price", Decimal("0")),
        ("quantity", 0),
    ],
)
def test_trade_rejects_invalid_values(field: str, value: object) -> None:
    values = {
        "event_id": "evt-000123",
        "event_type": "TRADE",
        "trade_id": "trd-000045",
        "symbol": "SIM",
        "price": Decimal("101.25"),
        "quantity": 40,
        "timestamp": TIMESTAMP,
    }

    values[field] = value

    with pytest.raises(ValueError):
        Trade(**values)


def test_analytics_result_creation() -> None:
    result = AnalyticsResult(
        event_id="evt-000201",
        event_type="ANALYTICS_UPDATE",
        symbol="SIM",
        price=Decimal("101.20"),
        vwap=Decimal("101.13"),
        sma=Decimal("101.10"),
        ema=Decimal("101.16"),
        position=150,
        realized_pnl=Decimal("120.00"),
        unrealized_pnl=Decimal("64.50"),
        equity=Decimal("10184.50"),
        peak_equity=Decimal("10210.00"),
        drawdown=Decimal("25.50"),
        timestamp=TIMESTAMP,
    )

    assert result.event_type == "ANALYTICS_UPDATE"
    assert result.vwap == Decimal("101.13")
    assert result.sma == Decimal("101.10")
    assert result.ema == Decimal("101.16")
    assert result.position == 150
    assert result.realized_pnl == Decimal("120.00")
    assert result.unrealized_pnl == Decimal("64.50")


def test_analytics_result_allows_missing_indicators() -> None:
    result = AnalyticsResult(
        event_id="evt-000201",
        event_type="ANALYTICS_UPDATE",
        symbol="SIM",
        price=Decimal("101.20"),
        vwap=None,
        sma=None,
        ema=None,
        position=0,
        realized_pnl=Decimal("0"),
        unrealized_pnl=Decimal("0"),
        equity=Decimal("10000"),
        peak_equity=Decimal("10000"),
        drawdown=Decimal("0"),
        timestamp=TIMESTAMP,
    )

    assert result.vwap is None
    assert result.sma is None
    assert result.ema is None


def test_analytics_result_to_dict() -> None:
    result = AnalyticsResult(
        event_id="evt-000201",
        event_type="ANALYTICS_UPDATE",
        symbol="SIM",
        price=Decimal("101.20"),
        vwap=Decimal("101.13"),
        sma=Decimal("101.10"),
        ema=Decimal("101.16"),
        position=150,
        realized_pnl=Decimal("120.00"),
        unrealized_pnl=Decimal("64.50"),
        equity=Decimal("10184.50"),
        peak_equity=Decimal("10210.00"),
        drawdown=Decimal("25.50"),
        timestamp=TIMESTAMP,
    )

    data = result.to_dict()

    assert data["event_type"] == "ANALYTICS_UPDATE"
    assert data["price"] == "101.20"
    assert data["vwap"] == "101.13"
    assert data["sma"] == "101.10"
    assert data["ema"] == "101.16"
    assert data["position"] == 150
    assert data["realized_pnl"] == "120.00"
    assert data["unrealized_pnl"] == "64.50"
    assert data["equity"] == "10184.50"
    assert data["peak_equity"] == "10210.00"
    assert data["drawdown"] == "25.50"


def test_analytics_result_rejects_invalid_values() -> None:
    common = {
        "event_id": "evt-000201",
        "event_type": "ANALYTICS_UPDATE",
        "symbol": "SIM",
        "price": Decimal("101.20"),
        "vwap": Decimal("101.13"),
        "sma": Decimal("101.10"),
        "ema": Decimal("101.16"),
        "position": 150,
        "realized_pnl": Decimal("120.00"),
        "unrealized_pnl": Decimal("64.50"),
        "equity": Decimal("10184.50"),
        "peak_equity": Decimal("10210.00"),
        "drawdown": Decimal("25.50"),
        "timestamp": TIMESTAMP,
    }

    invalid_cases = [
        {"event_id": ""},
        {"event_type": "TRADE"},
        {"symbol": ""},
        {"price": Decimal("0")},
        {"peak_equity": Decimal("10000")},
        {"drawdown": Decimal("-1")},
    ]

    for invalid in invalid_cases:
        values = common.copy()
        values.update(invalid)

        with pytest.raises(ValueError):
            AnalyticsResult(**values)
