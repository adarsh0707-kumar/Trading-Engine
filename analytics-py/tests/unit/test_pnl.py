"""Unit tests for P&L calculations."""

from decimal import Decimal

import pytest

from analytics.risk.pnl import (
    calculate_realized_pnl,
    calculate_unrealized_pnl,
)


def test_realized_pnl_for_long_position() -> None:
    result = calculate_realized_pnl(
        quantity=10,
        entry_price=Decimal("100"),
        exit_price=Decimal("110"),
        side="BUY",
    )

    assert result == Decimal("100")


def test_realized_pnl_for_long_loss() -> None:
    result = calculate_realized_pnl(
        quantity=10,
        entry_price=Decimal("100"),
        exit_price=Decimal("90"),
        side="BUY",
    )

    assert result == Decimal("-100")


def test_realized_pnl_for_short_position() -> None:
    result = calculate_realized_pnl(
        quantity=10,
        entry_price=Decimal("100"),
        exit_price=Decimal("90"),
        side="SELL",
    )

    assert result == Decimal("100")


def test_realized_pnl_for_short_loss() -> None:
    result = calculate_realized_pnl(
        quantity=10,
        entry_price=Decimal("100"),
        exit_price=Decimal("110"),
        side="SELL",
    )

    assert result == Decimal("-100")


def test_realized_pnl_rejects_invalid_side() -> None:
    with pytest.raises(ValueError, match="side must be BUY or SELL"):
        calculate_realized_pnl(
            quantity=10,
            entry_price=Decimal("100"),
            exit_price=Decimal("110"),
            side="HOLD",
        )


def test_realized_pnl_rejects_non_positive_quantity() -> None:
    with pytest.raises(ValueError, match="quantity must be positive"):
        calculate_realized_pnl(
            quantity=0,
            entry_price=Decimal("100"),
            exit_price=Decimal("110"),
            side="BUY",
        )


def test_unrealized_pnl_for_long_position() -> None:
    result = calculate_unrealized_pnl(
        position=10,
        average_entry_price=Decimal("100"),
        market_price=Decimal("110"),
    )

    assert result == Decimal("100")


def test_unrealized_pnl_for_short_position() -> None:
    result = calculate_unrealized_pnl(
        position=-10,
        average_entry_price=Decimal("100"),
        market_price=Decimal("90"),
    )

    assert result == Decimal("100")


def test_unrealized_pnl_can_be_negative() -> None:
    result = calculate_unrealized_pnl(
        position=10,
        average_entry_price=Decimal("100"),
        market_price=Decimal("90"),
    )

    assert result == Decimal("-100")


def test_unrealized_pnl_rejects_invalid_entry_price() -> None:
    with pytest.raises(ValueError, match="average_entry_price must be positive"):
        calculate_unrealized_pnl(
            position=10,
            average_entry_price=Decimal("0"),
            market_price=Decimal("100"),
        )


def test_unrealized_pnl_rejects_invalid_market_price() -> None:
    with pytest.raises(ValueError, match="market_price must be positive"):
        calculate_unrealized_pnl(
            position=10,
            average_entry_price=Decimal("100"),
            market_price=Decimal("0"),
        )
