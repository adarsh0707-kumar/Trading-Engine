"""Simple Moving Average (SMA) calculation."""

from __future__ import annotations

from decimal import Decimal
from typing import Iterable


def calculate_sma(
    prices: Iterable[Decimal],
    period: int,
) -> Decimal | None:
    """Calculate the latest Simple Moving Average.

    SMA is calculated as:

        SMA = sum(last N prices) / N

    where N is the requested period.

    Args:
        prices: Iterable of price observations.
        period: Number of observations in the moving window.

    Returns:
        The latest SMA when enough observations are available.
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

    window = price_list[-period:]

    return sum(window, Decimal("0")) / Decimal(period)