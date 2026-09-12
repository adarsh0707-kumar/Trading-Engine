"""Portfolio risk state management for streaming trade analytics."""

from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal

from analytics.risk.drawdown import calculate_drawdown, update_peak_equity
from analytics.risk.pnl import (
    calculate_realized_pnl,
    calculate_unrealized_pnl,
)
from analytics.risk.position_sizing import update_position


@dataclass(frozen=True, slots=True)
class RiskSnapshot:
    """Immutable snapshot of portfolio risk state."""

    position: int
    average_entry_price: Decimal | None
    realized_pnl: Decimal
    unrealized_pnl: Decimal
    equity: Decimal
    peak_equity: Decimal
    drawdown: Decimal


class RiskManager:
    """Maintain position, P&L, equity, and drawdown state."""

    def __init__(
        self,
        *,
        initial_equity: Decimal = Decimal("0"),
    ) -> None:
        if initial_equity < 0:
            raise ValueError("initial_equity must not be negative")

        self._position = 0
        self._average_entry_price: Decimal | None = None
        self._realized_pnl = Decimal("0")
        self._initial_equity = initial_equity
        self._equity = initial_equity
        self._peak_equity = initial_equity
        self._unrealized_pnl = Decimal("0")
        self._drawdown = Decimal("0")

    @property
    def position(self) -> int:
        """Return the current signed position."""
        return self._position

    @property
    def average_entry_price(self) -> Decimal | None:
        """Return the current average entry price."""
        return self._average_entry_price

    def process_trade(
        self,
        *,
        quantity: int,
        price: Decimal,
        side: str,
    ) -> RiskSnapshot:
        """Apply a trade and return the resulting risk snapshot.

        BUY increases a long position or reduces a short position.
        SELL increases a short position or reduces a long position.

        When an existing position is reduced or closed, realized P&L is
        calculated using the existing average entry price. When a position
        is opened or increased, the average entry price is recalculated
        using quantity-weighted averaging.
        """
        if quantity <= 0:
            raise ValueError("quantity must be positive")

        if price <= 0:
            raise ValueError("price must be positive")

        normalized_side = side.upper()

        if normalized_side not in {"BUY", "SELL"}:
            raise ValueError("side must be BUY or SELL")

        signed_quantity = quantity if normalized_side == "BUY" else -quantity

        self._apply_trade(
            signed_quantity=signed_quantity,
            price=price,
        )

        self._unrealized_pnl = self._calculate_unrealized(price)

        self._equity = (
            self._initial_equity
            + self._realized_pnl
            + self._unrealized_pnl
        )

        self._peak_equity = update_peak_equity(
            equity=self._equity,
            peak_equity=self._peak_equity,
        )

        self._drawdown = calculate_drawdown(
            equity=self._equity,
            peak_equity=self._peak_equity,
        )

        return self.snapshot()

    def snapshot(self) -> RiskSnapshot:
        """Return the current immutable risk snapshot."""
        return RiskSnapshot(
            position=self._position,
            average_entry_price=self._average_entry_price,
            realized_pnl=self._realized_pnl,
            unrealized_pnl=self._unrealized_pnl,
            equity=self._equity,
            peak_equity=self._peak_equity,
            drawdown=self._drawdown,
        )

    def _apply_trade(
        self,
        *,
        signed_quantity: int,
        price: Decimal,
    ) -> None:
        """Apply signed quantity to the current position."""
        current = self._position

        if current == 0:
            self._position = signed_quantity
            self._average_entry_price = price
            return

        same_direction = (
            (current > 0 and signed_quantity > 0)
            or (current < 0 and signed_quantity < 0)
        )

        if same_direction:
            self._increase_position(
                signed_quantity=signed_quantity,
                price=price,
            )
            return

        self._reduce_or_reverse(
            signed_quantity=signed_quantity,
            price=price,
        )

    def _increase_position(
        self,
        *,
        signed_quantity: int,
        price: Decimal,
    ) -> None:
        """Increase an existing position in the same direction."""
        assert self._average_entry_price is not None

        current_abs = abs(self._position)
        trade_abs = abs(signed_quantity)
        total_abs = current_abs + trade_abs

        self._average_entry_price = (
            (
                self._average_entry_price * Decimal(current_abs)
                + price * Decimal(trade_abs)
            )
            / Decimal(total_abs)
        )

        self._position += signed_quantity

    def _reduce_or_reverse(
        self,
        *,
        signed_quantity: int,
        price: Decimal,
    ) -> None:
        """Reduce, close, or reverse the current position."""
        assert self._average_entry_price is not None

        current_abs = abs(self._position)
        trade_abs = abs(signed_quantity)
        closing_quantity = min(current_abs, trade_abs)

        if self._position > 0:
            realized = calculate_realized_pnl(
                quantity=closing_quantity,
                entry_price=self._average_entry_price,
                exit_price=price,
                side="BUY",
            )
        else:
            realized = calculate_realized_pnl(
                quantity=closing_quantity,
                entry_price=self._average_entry_price,
                exit_price=price,
                side="SELL",
            )

        self._realized_pnl += realized

        new_position = self._position + signed_quantity

        if new_position == 0:
            self._position = 0
            self._average_entry_price = None
            return

        if (self._position > 0 and new_position > 0) or (
            self._position < 0 and new_position < 0
        ):
            self._position = new_position
            return

        self._position = new_position
        self._average_entry_price = price

    def _calculate_unrealized(self, market_price: Decimal) -> Decimal:
        """Calculate unrealized P&L using the current market price."""
        if self._position == 0:
            return Decimal("0")

        assert self._average_entry_price is not None

        return calculate_unrealized_pnl(
            position=self._position,
            average_entry_price=self._average_entry_price,
            market_price=market_price,
        )


__all__ = [
    "RiskManager",
    "RiskSnapshot",
]
