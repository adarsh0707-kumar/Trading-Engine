"""Exponential Moving Average (EMA) calculation."""

from __future__ import annotations

from decimal import Decimal
from typing import Iterable


def calculate_ema(
    prices: Iterable[Decimal],
    period: int,
) -> Decimal | None:
    """Calculate the latest Exponential Moving Average.

    The first EMA value is initialized using the SMA of the first
    ``period`` observations.

    Subsequent values use:

        EMA = alpha * price + (1 - alpha) * previous EMA

    where:

        alpha = 2 / (period + 1)

    Args:
        prices: Iterable of price observations.
        period: Number of observations used for EMA initialization.

    Returns:
        The latest EMA when enough observations are available.
        Returns None when fewer than ``period`` observations exist.

    Raises:
        ValueError: If period is not positive or prices are empty.
    """

    price_list = list(prices)

    if period <= 0:
        raise ValueError("period must be positive")

    if not price_list:
        raise ValueError("prices must not be empty")

    if len(price_list) < period:
        return None

    period_decimal = Decimal(period)
    alpha = Decimal("2") / (period_decimal + Decimal("1"))

    ema = sum(price_list[:period], Decimal("0")) / period_decimal

    for price in price_list[period:]:
        ema = (alpha * price) + ((Decimal("1") - alpha) * ema)

    return ema