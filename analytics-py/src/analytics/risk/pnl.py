"""Profit and loss calculations for streaming trading analytics."""

from __future__ import annotations

from decimal import Decimal


def calculate_realized_pnl(
    *,
    quantity: int,
    entry_price: Decimal,
    exit_price: Decimal,
    side: str,
) -> Decimal:
    """Calculate realized P&L for a completed position.

    BUY positions profit when the exit price is above the entry price.
    SELL positions profit when the exit price is below the entry price.

    Args:
        quantity: Absolute quantity closed.
        entry_price: Average entry price.
        exit_price: Exit/fill price.
        side: Position side, either ``BUY`` or ``SELL``.

    Returns:
        Realized P&L as a Decimal.

    Raises:
        ValueError: If inputs are invalid or side is unknown.
    """
    if quantity <= 0:
        raise ValueError("quantity must be positive")

    if entry_price <= 0:
        raise ValueError("entry_price must be positive")

    if exit_price <= 0:
        raise ValueError("exit_price must be positive")

    normalized_side = side.upper()

    if normalized_side == "BUY":
        return (exit_price - entry_price) * Decimal(quantity)

    if normalized_side == "SELL":
        return (entry_price - exit_price) * Decimal(quantity)

    raise ValueError("side must be BUY or SELL")


def calculate_unrealized_pnl(
    *,
    position: int,
    average_entry_price: Decimal,
    market_price: Decimal,
) -> Decimal:
    """Calculate unrealized P&L for an open position.

    A positive position represents a long position.
    A negative position represents a short position.

    Args:
        position: Signed open quantity.
        average_entry_price: Average price of the open position.
        market_price: Current market price.

    Returns:
        Unrealized P&L as a Decimal.

    Raises:
        ValueError: If either price is not positive.
    """
    if average_entry_price <= 0:
        raise ValueError("average_entry_price must be positive")

    if market_price <= 0:
        raise ValueError("market_price must be positive")

    return (market_price - average_entry_price) * Decimal(position)


__all__ = [
    "calculate_realized_pnl",
    "calculate_unrealized_pnl",
]
