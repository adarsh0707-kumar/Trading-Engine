"""Rolling price-return volatility calculation."""

from __future__ import annotations

from decimal import Decimal
from typing import Iterable


def calculate_volatility(
    prices: Iterable[Decimal],
    period: int,
) -> Decimal | None:
    """Calculate rolling sample standard deviation of simple returns.

    A simple return is calculated as:

        return = (current_price - previous_price) / previous_price

    Volatility is the sample standard deviation of the latest ``period``
    returns.

    Args:
        prices: Iterable of positive price observations.
        period: Number of returns included in the volatility window.

    Returns:
        The latest rolling volatility when enough observations are
        available. Returns None when fewer than ``period + 1`` prices
        exist.

    Raises:
        ValueError: If period is not positive, prices are empty, or a
            price is not positive.
    """

    price_list = list(prices)

    if period <= 0:
        raise ValueError("period must be positive")

    if not price_list:
        raise ValueError("prices must not be empty")

    if any(price <= 0 for price in price_list):
        raise ValueError("prices must be positive")

    if len(price_list) < period + 1:
        return None

    returns = [
        (current - previous) / previous
        for previous, current in zip(
            price_list,
            price_list[1:],
        )
    ]

    window = returns[-period:]

    if len(window) < 2:
        return Decimal("0")

    mean = sum(window, Decimal("0")) / Decimal(len(window))

    squared_deviations = [
        (value - mean) ** 2
        for value in window
    ]

    variance = sum(
        squared_deviations,
        Decimal("0"),
    ) / Decimal(len(window) - 1)

    return variance.sqrt()
