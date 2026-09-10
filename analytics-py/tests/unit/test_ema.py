"""Unit tests for EMA calculation."""

from decimal import Decimal

import pytest

from analytics.indicators.ema import calculate_ema


def test_calculate_ema_initializes_with_sma() -> None:
    prices = [
        Decimal("100.00"),
        Decimal("101.00"),
        Decimal("102.00"),
    ]

    result = calculate_ema(prices, 3)

    assert result == Decimal("101.00")


def test_calculate_ema_applies_recursive_formula() -> None:
    prices = [
        Decimal("100.00"),
        Decimal("101.00"),
        Decimal("102.00"),
        Decimal("104.00"),
    ]

    result = calculate_ema(prices, 3)

    # Initial SMA = (100 + 101 + 102) / 3 = 101
    #
    # alpha = 2 / (3 + 1) = 0.5
    #
    # EMA = 0.5 * 104 + 0.5 * 101 = 102.5
    assert result == Decimal("102.50")


def test_calculate_ema_uses_all_observations_after_initialization() -> None:
    prices = [
        Decimal("100.00"),
        Decimal("102.00"),
        Decimal("104.00"),
        Decimal("108.00"),
        Decimal("112.00"),
    ]

    result = calculate_ema(prices, 3)

    # Initial SMA = 102
    # EMA(108) = 0.5 * 108 + 0.5 * 102 = 105
    # EMA(112) = 0.5 * 112 + 0.5 * 105 = 108.5
    assert result == Decimal("108.50")


def test_calculate_ema_single_period() -> None:
    prices = [
        Decimal("100.00"),
        Decimal("105.00"),
        Decimal("110.00"),
    ]

    result = calculate_ema(prices, 1)

    assert result == Decimal("110.00")


def test_calculate_ema_returns_none_until_window_is_full() -> None:
    prices = [
        Decimal("100.00"),
        Decimal("101.00"),
    ]

    assert calculate_ema(prices, 3) is None


@pytest.mark.parametrize("period", [0, -1, -5])
def test_calculate_ema_rejects_invalid_period(period: int) -> None:
    with pytest.raises(ValueError):
        calculate_ema([Decimal("100.00")], period)


def test_calculate_ema_rejects_empty_prices() -> None:
    with pytest.raises(ValueError):
        calculate_ema([], 3)