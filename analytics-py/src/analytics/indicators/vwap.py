"""Volume Weighted Average Price (VWAP) calculation."""

from __future__ import annotations

from decimal import Decimal
from typing import Iterable


def calculate_vwap(
    prices: Iterable[Decimal],
    quantities: Iterable[int],
) -> Decimal:
    """Calculate the Volume Weighted Average Price.

    VWAP is calculated as:

        VWAP = sum(price * quantity) / sum(quantity)

    Args:
        prices: Iterable of trade or tick prices.
        quantities: Iterable of corresponding quantities.

    Returns:
        The volume weighted average price.

    Raises:
        ValueError: If the inputs are empty, have different lengths,
            contain non-positive quantities, or have zero total volume.
    """

    price_list = list(prices)
    quantity_list = list(quantities)

    if not price_list:
        raise ValueError("prices must not be empty")

    if len(price_list) != len(quantity_list):
        raise ValueError("prices and quantities must have the same length")

    if any(quantity <= 0 for quantity in quantity_list):
        raise ValueError("quantities must be positive")

    total_quantity = sum(quantity_list)

    if total_quantity <= 0:
        raise ValueError("total quantity must be positive")

    total_value = sum(
        price * quantity
        for price, quantity in zip(price_list, quantity_list)
    )

    return total_value / Decimal(total_quantity)
