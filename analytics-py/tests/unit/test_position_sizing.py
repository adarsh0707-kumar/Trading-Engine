"""Unit tests for position-state calculations."""

from decimal import Decimal

import pytest

from analytics.risk.position_sizing import (
    calculate_position_value,
    update_position,
)


def test_buy_increases_long_position() -> None:
    result = update_position(
        current_position=0,
        quantity=10,
        side="BUY",
    )

    assert result == 10


def test_sell_decreases_position() -> None:
    result = update_position(
        current_position=10,
        quantity=4,
        side="SELL",
    )

    assert result == 6


def test_sell_can_create_short_position() -> None:
    result = update_position(
        current_position=0,
        quantity=10,
        side="SELL",
    )

    assert result == -10


def test_buy_can_reduce_short_position() -> None:
    result = update_position(
        current_position=-10,
        quantity=4,
        side="BUY",
    )

    assert result == -6


def test_position_update_accepts_lowercase_side() -> None:
    assert update_position(
        current_position=0,
        quantity=5,
        side="buy",
    ) == 5


def test_position_update_rejects_zero_quantity() -> None:
    with pytest.raises(ValueError, match="quantity must be positive"):
        update_position(
            current_position=0,
            quantity=0,
            side="BUY",
        )


def test_position_update_rejects_negative_quantity() -> None:
    with pytest.raises(ValueError, match="quantity must be positive"):
        update_position(
            current_position=0,
            quantity=-5,
            side="BUY",
        )


def test_position_update_rejects_unknown_side() -> None:
    with pytest.raises(ValueError, match="side must be BUY or SELL"):
        update_position(
            current_position=0,
            quantity=5,
            side="HOLD",
        )


def test_position_value_for_long_position() -> None:
    result = calculate_position_value(
        position=10,
        market_price=Decimal("125.50"),
    )

    assert result == Decimal("1255.00")


def test_position_value_for_short_position() -> None:
    result = calculate_position_value(
        position=-10,
        market_price=Decimal("125.50"),
    )

    assert result == Decimal("-1255.00")


def test_zero_position_has_zero_value() -> None:
    result = calculate_position_value(
        position=0,
        market_price=Decimal("125.50"),
    )

    assert result == Decimal("0.00")


def test_position_value_rejects_non_positive_price() -> None:
    with pytest.raises(ValueError, match="market_price must be positive"):
        calculate_position_value(
            position=10,
            market_price=Decimal("0"),
        )
