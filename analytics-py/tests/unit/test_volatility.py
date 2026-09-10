"""Unit tests for volatility calculation."""

from decimal import Decimal

import pytest

from analytics.indicators.volatility import calculate_volatility


def test_calculate_volatility() -> None:
    prices = [
        Decimal("100.00"),
        Decimal("102.00"),
        Decimal("101.00"),
        Decimal("104.00"),
    ]

    result = calculate_volatility(prices, 3)

    returns = [
        Decimal("2") / Decimal("100"),
        Decimal("-1") / Decimal("102"),
        Decimal("3") / Decimal("101"),
    ]

    mean = sum(returns, Decimal("0")) / Decimal("3")

    variance = sum(
        (value - mean) ** 2
        for value in returns
    ) / Decimal("2")

    expected = variance.sqrt()

    assert result == expected


def test_calculate_volatility_constant_returns() -> None:
    prices = [
        Decimal("100.00"),
        Decimal("101.00"),
        Decimal("102.01"),
        Decimal("103.0301"),
    ]

    result = calculate_volatility(prices, 3)

    assert result < Decimal("0.000001")


def test_calculate_volatility_uses_latest_window() -> None:
    prices = [
        Decimal("100.00"),
        Decimal("101.00"),
        Decimal("102.00"),
        Decimal("103.00"),
        Decimal("120.00"),
    ]

    result = calculate_volatility(prices, 2)

    latest_returns = [
        (Decimal("103.00") - Decimal("102.00")) / Decimal("102.00"),
        (Decimal("120.00") - Decimal("103.00")) / Decimal("103.00"),
    ]

    mean = sum(latest_returns, Decimal("0")) / Decimal("2")

    expected = (
        sum(
            (value - mean) ** 2
            for value in latest_returns
        )
        / Decimal("1")
    ).sqrt()

    assert result == expected


def test_calculate_volatility_returns_none_until_window_is_full() -> None:
    prices = [
        Decimal("100.00"),
        Decimal("101.00"),
    ]

    assert calculate_volatility(prices, 3) is None


def test_calculate_volatility_period_one_returns_zero() -> None:
    prices = [
        Decimal("100.00"),
        Decimal("105.00"),
    ]

    result = calculate_volatility(prices, 1)

    assert result == Decimal("0")


@pytest.mark.parametrize("period", [0, -1, -5])
def test_calculate_volatility_rejects_invalid_period(
    period: int,
) -> None:
    with pytest.raises(ValueError):
        calculate_volatility(
            [Decimal("100.00"), Decimal("101.00")],
            period,
        )


def test_calculate_volatility_rejects_empty_prices() -> None:
    with pytest.raises(ValueError):
        calculate_volatility([], 3)


@pytest.mark.parametrize(
    "prices",
    [
        [Decimal("0"), Decimal("100.00")],
        [Decimal("100.00"), Decimal("0")],
        [Decimal("100.00"), Decimal("-1.00")],
    ],
)
def test_calculate_volatility_rejects_non_positive_prices(
    prices: list[Decimal],
) -> None:
    with pytest.raises(ValueError):
        calculate_volatility(prices, 1)
