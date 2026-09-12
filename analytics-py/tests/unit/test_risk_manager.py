"""Unit tests for portfolio risk management."""

from decimal import Decimal

import pytest

from analytics.risk.risk_manager import RiskManager


def test_buy_opens_long_position() -> None:
    manager = RiskManager(initial_equity=Decimal("10000"))

    snapshot = manager.process_trade(
        quantity=10,
        price=Decimal("100"),
        side="BUY",
    )

    assert snapshot.position == 10
    assert snapshot.average_entry_price == Decimal("100")
    assert snapshot.realized_pnl == Decimal("0")
    assert snapshot.unrealized_pnl == Decimal("0")
    assert snapshot.equity == Decimal("10000")


def test_buy_increases_position_with_weighted_average() -> None:
    manager = RiskManager(initial_equity=Decimal("10000"))

    manager.process_trade(
        quantity=10,
        price=Decimal("100"),
        side="BUY",
    )

    snapshot = manager.process_trade(
        quantity=10,
        price=120,
        side="BUY",
    )

    assert snapshot.position == 20
    assert snapshot.average_entry_price == Decimal("110")


def test_sell_reduces_long_and_realizes_profit() -> None:
    manager = RiskManager(initial_equity=Decimal("10000"))

    manager.process_trade(
        quantity=10,
        price=Decimal("100"),
        side="BUY",
    )

    snapshot = manager.process_trade(
        quantity=4,
        price=Decimal("120"),
        side="SELL",
    )

    assert snapshot.position == 6
    assert snapshot.average_entry_price == Decimal("100")
    assert snapshot.realized_pnl == Decimal("80")
    assert snapshot.unrealized_pnl == Decimal("120")
    assert snapshot.equity == Decimal("10200")


def test_sell_reduces_long_and_realizes_loss() -> None:
    manager = RiskManager(initial_equity=Decimal("10000"))

    manager.process_trade(
        quantity=10,
        price=Decimal("100"),
        side="BUY",
    )

    snapshot = manager.process_trade(
        quantity=4,
        price=Decimal("80"),
        side="SELL",
    )

    assert snapshot.position == 6
    assert snapshot.realized_pnl == Decimal("-80")
    assert snapshot.unrealized_pnl == Decimal("-120")
    assert snapshot.equity == Decimal("9800")


def test_closing_long_position_clears_entry_price() -> None:
    manager = RiskManager(initial_equity=Decimal("10000"))

    manager.process_trade(
        quantity=10,
        price=Decimal("100"),
        side="BUY",
    )

    snapshot = manager.process_trade(
        quantity=10,
        price=Decimal("110"),
        side="SELL",
    )

    assert snapshot.position == 0
    assert snapshot.average_entry_price is None
    assert snapshot.realized_pnl == Decimal("100")
    assert snapshot.unrealized_pnl == Decimal("0")
    assert snapshot.equity == Decimal("10100")


def test_sell_opens_short_position() -> None:
    manager = RiskManager(initial_equity=Decimal("10000"))

    snapshot = manager.process_trade(
        quantity=10,
        price=Decimal("100"),
        side="SELL",
    )

    assert snapshot.position == -10
    assert snapshot.average_entry_price == Decimal("100")
    assert snapshot.realized_pnl == Decimal("0")
    assert snapshot.unrealized_pnl == Decimal("0")


def test_buy_reduces_short_and_realizes_profit() -> None:
    manager = RiskManager(initial_equity=Decimal("10000"))

    manager.process_trade(
        quantity=10,
        price=Decimal("100"),
        side="SELL",
    )

    snapshot = manager.process_trade(
        quantity=4,
        price=Decimal("80"),
        side="BUY",
    )

    assert snapshot.position == -6
    assert snapshot.average_entry_price == Decimal("100")
    assert snapshot.realized_pnl == Decimal("80")
    assert snapshot.unrealized_pnl == Decimal("120")


def test_buy_reduces_short_and_realizes_loss() -> None:
    manager = RiskManager(initial_equity=Decimal("10000"))

    manager.process_trade(
        quantity=10,
        price=Decimal("100"),
        side="SELL",
    )

    snapshot = manager.process_trade(
        quantity=4,
        price=Decimal("120"),
        side="BUY",
    )

    assert snapshot.position == -6
    assert snapshot.realized_pnl == Decimal("-80")
    assert snapshot.unrealized_pnl == Decimal("-120")


def test_position_reversal_from_long_to_short() -> None:
    manager = RiskManager(initial_equity=Decimal("10000"))

    manager.process_trade(
        quantity=10,
        price=Decimal("100"),
        side="BUY",
    )

    snapshot = manager.process_trade(
        quantity=15,
        price=Decimal("110"),
        side="SELL",
    )

    assert snapshot.position == -5
    assert snapshot.average_entry_price == Decimal("110")
    assert snapshot.realized_pnl == Decimal("100")
    assert snapshot.unrealized_pnl == Decimal("0")


def test_position_reversal_from_short_to_long() -> None:
    manager = RiskManager(initial_equity=Decimal("10000"))

    manager.process_trade(
        quantity=10,
        price=Decimal("100"),
        side="SELL",
    )

    snapshot = manager.process_trade(
        quantity=15,
        price=Decimal("90"),
        side="BUY",
    )

    assert snapshot.position == 5
    assert snapshot.average_entry_price == Decimal("90")
    assert snapshot.realized_pnl == Decimal("100")
    assert snapshot.unrealized_pnl == Decimal("0")


def test_drawdown_tracks_equity_decline() -> None:
    manager = RiskManager(initial_equity=Decimal("10000"))

    manager.process_trade(
        quantity=10,
        price=Decimal("100"),
        side="BUY",
    )

    snapshot = manager.process_trade(
        quantity=10,
        price=Decimal("80"),
        side="SELL",
    )

    assert snapshot.realized_pnl == Decimal("-200")
    assert snapshot.equity == Decimal("9800")
    assert snapshot.peak_equity == Decimal("10000")
    assert snapshot.drawdown == Decimal("200")


def test_invalid_side_is_rejected() -> None:
    manager = RiskManager(initial_equity=Decimal("10000"))

    with pytest.raises(ValueError, match="side must be BUY or SELL"):
        manager.process_trade(
            quantity=10,
            price=Decimal("100"),
            side="HOLD",
        )


def test_invalid_quantity_is_rejected() -> None:
    manager = RiskManager(initial_equity=Decimal("10000"))

    with pytest.raises(ValueError, match="quantity must be positive"):
        manager.process_trade(
            quantity=0,
            price=Decimal("100"),
            side="BUY",
        )


def test_invalid_price_is_rejected() -> None:
    manager = RiskManager(initial_equity=Decimal("10000"))

    with pytest.raises(ValueError, match="price must be positive"):
        manager.process_trade(
            quantity=10,
            price=Decimal("0"),
            side="BUY",
        )
