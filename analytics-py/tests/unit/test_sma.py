"""Unit tests for SMA calculation."""

from decimal import Decimal

import pytest

from analytics.indicators.sma import calculate_sma


def test_calculate_sma() -> None:
    prices = [
        Decimal("100.00"),
        Decimal("101.00"),
        Decimal("102.00"),
    ]

    result = calculate_sma(prices, 3)

    assert result == Decimal("101.00")


def test_calculate_sma_uses_latest_window() -> None:
    prices = [
        Decimal("100.00"),
        Decimal("101.00"),
        Decimal("102.00"),
        Decimal("103.00"),
        Decimal("104.00"),
    ]

    result = calculate_sma(prices, 3)

    assert result == Decimal("103.00")


def test_calculate_sma_single_period() -> None:
    prices = [
        Decimal("100.00"),
        Decimal("105.50"),
        Decimal("110.00"),
    ]

    result = calculate_sma(prices, 1)

    assert result == Decimal("110.00")


def test_calculate_sma_returns_none_until_window_is_full() -> None:
    prices = [
        Decimal("100.00"),
        Decimal("101.00"),
    ]

    assert calculate_sma(prices, 3) is None


@pytest.mark.parametrize("period", [0, -1, -5])
def test_calculate_sma_rejects_invalid_period(period: int) -> None:
    with pytest.raises(ValueError):
        calculate_sma([Decimal("100.00")], period)


def test_calculate_sma_rejects_empty_prices() -> None:
    with pytest.raises(ValueError):
        calculate_sma([], 3)