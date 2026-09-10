"""Unit tests for VWAP calculation."""

from decimal import Decimal

import pytest

from analytics.indicators import calculate_vwap


def test_calculate_vwap() -> None:
    prices = [
        Decimal("100.00"),
        Decimal("101.00"),
        Decimal("102.00"),
    ]
    quantities = [10, 20, 30]

    result = calculate_vwap(prices, quantities)

    # (100*10 + 101*20 + 102*30) / 60 = 101.333333...
    assert result == Decimal("6080") / Decimal("60")


def test_calculate_vwap_single_observation() -> None:
    result = calculate_vwap(
        [Decimal("101.25")],
        [40],
    )

    assert result == Decimal("101.25")


def test_calculate_vwap_uses_volume_weighting() -> None:
    result = calculate_vwap(
        [
            Decimal("100.00"),
            Decimal("110.00"),
        ],
        [90, 10],
    )

    assert result == Decimal("101.00")


@pytest.mark.parametrize(
    ("prices", "quantities"),
    [
        ([], []),
        ([Decimal("100.00")], []),
        ([Decimal("100.00")], [0]),
        ([Decimal("100.00")], [-1]),
    ],
)
def test_calculate_vwap_rejects_invalid_input(
    prices: list[Decimal],
    quantities: list[int],
) -> None:
    with pytest.raises(ValueError):
        calculate_vwap(prices, quantities)
