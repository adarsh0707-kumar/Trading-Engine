"""Unit tests for drawdown calculations."""

from decimal import Decimal

import pytest

from analytics.risk.drawdown import (
    calculate_drawdown,
    update_peak_equity,
)


def test_drawdown_is_zero_at_peak() -> None:
    result = calculate_drawdown(
        equity=Decimal("1000"),
        peak_equity=Decimal("1000"),
    )

    assert result == Decimal("0")


def test_drawdown_is_peak_minus_equity() -> None:
    result = calculate_drawdown(
        equity=Decimal("850"),
        peak_equity=Decimal("1000"),
    )

    assert result == Decimal("150")


def test_drawdown_preserves_decimal_precision() -> None:
    result = calculate_drawdown(
        equity=Decimal("987.65"),
        peak_equity=Decimal("1000.25"),
    )

    assert result == Decimal("12.60")


def test_drawdown_rejects_peak_below_equity() -> None:
    with pytest.raises(
        ValueError,
        match="peak_equity must be greater than or equal to equity",
    ):
        calculate_drawdown(
            equity=Decimal("1100"),
            peak_equity=Decimal("1000"),
        )


def test_drawdown_rejects_negative_equity() -> None:
    with pytest.raises(ValueError, match="equity must not be negative"):
        calculate_drawdown(
            equity=Decimal("-100"),
            peak_equity=Decimal("1000"),
        )


def test_drawdown_rejects_negative_peak() -> None:
    with pytest.raises(ValueError, match="peak_equity must not be negative"):
        calculate_drawdown(
            equity=Decimal("0"),
            peak_equity=Decimal("-100"),
        )


def test_peak_equity_updates_when_equity_increases() -> None:
    result = update_peak_equity(
        equity=Decimal("1200"),
        peak_equity=Decimal("1000"),
    )

    assert result == Decimal("1200")


def test_peak_equity_is_preserved_when_equity_decreases() -> None:
    result = update_peak_equity(
        equity=Decimal("900"),
        peak_equity=Decimal("1000"),
    )

    assert result == Decimal("1000")


def test_peak_equity_is_preserved_at_same_value() -> None:
    result = update_peak_equity(
        equity=Decimal("1000"),
        peak_equity=Decimal("1000"),
    )

    assert result == Decimal("1000")


def test_peak_equity_rejects_negative_equity() -> None:
    with pytest.raises(ValueError, match="equity must not be negative"):
        update_peak_equity(
            equity=Decimal("-1"),
            peak_equity=Decimal("1000"),
        )


def test_peak_equity_rejects_negative_previous_peak() -> None:
    with pytest.raises(ValueError, match="peak_equity must not be negative"):
        update_peak_equity(
            equity=Decimal("1000"),
            peak_equity=Decimal("-1"),
        )
