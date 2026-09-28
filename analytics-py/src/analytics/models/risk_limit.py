"""Domain models for risk-limit evaluation."""

from dataclasses import dataclass
from decimal import Decimal
from enum import StrEnum


class RiskLimitType(StrEnum):
    """Supported risk-limit categories."""

    MAX_POSITION = "max_position"
    MAX_POSITION_VALUE = "max_position_value"
    MAX_DRAWDOWN = "max_drawdown"
    MAX_DAILY_LOSS = "max_daily_loss"


class RiskLimitStatus(StrEnum):
    """Current status of a risk limit."""

    OK = "ok"
    WARNING = "warning"
    BREACHED = "breached"


@dataclass(frozen=True, slots=True)
class RiskLimit:
    """A single evaluated risk threshold."""

    limit_type: RiskLimitType
    threshold: Decimal
    warning_threshold: Decimal
    symbol: str | None = None

    def __post_init__(self) -> None:
        """Validate the risk-limit definition."""
        if self.threshold <= Decimal("0"):
            raise ValueError("threshold must be greater than zero")

        if self.warning_threshold <= Decimal("0"):
            raise ValueError("warning_threshold must be greater than zero")

        if self.warning_threshold >= self.threshold:
            raise ValueError(
                "warning_threshold must be less than threshold"
            )

        if self.symbol is not None and not self.symbol.strip():
            raise ValueError("symbol must not be blank")


@dataclass(frozen=True, slots=True)
class RiskLimitState:
    """Current value and status for a risk limit."""

    limit: RiskLimit
    current_value: Decimal
    status: RiskLimitStatus

    def __post_init__(self) -> None:
        """Validate the current risk-limit state."""
        if self.current_value < Decimal("0"):
            raise ValueError("current_value must not be negative")
