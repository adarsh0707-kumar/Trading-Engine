"""Risk-limit configuration for the analytics service."""

from dataclasses import dataclass
from decimal import Decimal


@dataclass(frozen=True, slots=True)
class RiskLimitConfig:
    """Configurable thresholds used by the risk engine.

    All monetary values are represented using Decimal to avoid floating-point
    precision issues.
    """

    max_position: int | None = None
    max_position_value: Decimal | None = None
    max_drawdown: Decimal | None = None
    max_daily_loss: Decimal | None = None
    warning_ratio: Decimal = Decimal("0.80")

    def __post_init__(self) -> None:
        """Validate risk-limit configuration values."""
        if self.max_position is not None and self.max_position <= 0:
            raise ValueError("max_position must be greater than zero")

        monetary_limits = {
            "max_position_value": self.max_position_value,
            "max_drawdown": self.max_drawdown,
            "max_daily_loss": self.max_daily_loss,
        }

        for name, value in monetary_limits.items():
            if value is not None and value <= Decimal("0"):
                raise ValueError(f"{name} must be greater than zero")

        if not Decimal("0") < self.warning_ratio < Decimal("1"):
            raise ValueError("warning_ratio must be greater than 0 and less than 1")
