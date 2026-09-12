"""Drawdown calculations for streaming trading analytics."""

from __future__ import annotations

from decimal import Decimal


def calculate_drawdown(
    *,
    equity: Decimal,
    peak_equity: Decimal,
) -> Decimal:
    """Calculate absolute drawdown from peak equity.

    Drawdown is the difference between the historical peak equity and
    the current equity. It is never negative.

    Args:
        equity: Current account equity.
        peak_equity: Highest equity observed so far.

    Returns:
        Absolute drawdown as a Decimal.

    Raises:
        ValueError: If peak equity is negative or below current equity.
    """
    if peak_equity < 0:
        raise ValueError("peak_equity must not be negative")

    if equity < 0:
        raise ValueError("equity must not be negative")

    if peak_equity < equity:
        raise ValueError(
            "peak_equity must be greater than or equal to equity"
        )

    return peak_equity - equity


def update_peak_equity(
    *,
    equity: Decimal,
    peak_equity: Decimal,
) -> Decimal:
    """Return the updated peak equity.

    If current equity exceeds the previous peak, current equity becomes
    the new peak. Otherwise the existing peak is preserved.

    Args:
        equity: Current account equity.
        peak_equity: Previously recorded peak equity.

    Returns:
        Updated peak equity.

    Raises:
        ValueError: If either value is negative.
    """
    if equity < 0:
        raise ValueError("equity must not be negative")

    if peak_equity < 0:
        raise ValueError("peak_equity must not be negative")

    return max(equity, peak_equity)


__all__ = [
    "calculate_drawdown",
    "update_peak_equity",
]
