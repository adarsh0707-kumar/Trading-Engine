"""Position sizing and position-state calculations."""

from __future__ import annotations


def update_position(
    *,
    current_position: int,
    quantity: int,
    side: str,
) -> int:
    """Apply a trade quantity to a signed position.

    BUY increases the position.
    SELL decreases the position.

    Args:
        current_position: Existing signed position.
        quantity: Positive trade quantity.
        side: Trade side, either ``BUY`` or ``SELL``.

    Returns:
        Updated signed position.

    Raises:
        ValueError: If quantity is invalid or side is unknown.
    """
    if quantity <= 0:
        raise ValueError("quantity must be positive")

    normalized_side = side.upper()

    if normalized_side == "BUY":
        return current_position + quantity

    if normalized_side == "SELL":
        return current_position - quantity

    raise ValueError("side must be BUY or SELL")


def calculate_position_value(
    *,
    position: int,
    market_price,
) -> object:
    """Calculate the mark-to-market value of a position.

    The result uses the same numeric type as ``market_price``. The
    function intentionally accepts Decimal-compatible values so the
    caller can keep financial calculations in Decimal arithmetic.

    Args:
        position: Signed position quantity.
        market_price: Current market price.

    Returns:
        Position value.

    Raises:
        ValueError: If market price is not positive.
    """
    if market_price <= 0:
        raise ValueError("market_price must be positive")

    return position * market_price


__all__ = [
    "update_position",
    "calculate_position_value",
]
