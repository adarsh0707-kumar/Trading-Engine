"""Risk-limit evaluation for streaming trading analytics."""

from __future__ import annotations

from decimal import Decimal

from analytics.config.risk_limits import RiskLimitConfig
from analytics.models.risk_limit import (
    RiskLimit,
    RiskLimitState,
    RiskLimitStatus,
    RiskLimitType,
)
from analytics.risk.position_sizing import calculate_position_value
from analytics.risk.risk_manager import RiskSnapshot


class RiskLimitEvaluator:
    """Evaluate configured risk limits against the current risk state."""

    def __init__(self, config: RiskLimitConfig) -> None:
        """Initialize the evaluator with risk-limit configuration."""
        self._config = config

    def evaluate(
        self,
        *,
        snapshot: RiskSnapshot,
        market_price: Decimal,
        daily_loss: Decimal = Decimal("0"),
        symbol: str | None = None,
    ) -> tuple[RiskLimitState, ...]:
        """Evaluate all enabled risk limits.

        Args:
            snapshot: Current portfolio risk snapshot.
            market_price: Current market price used for position valuation.
            daily_loss: Current absolute daily loss.
            symbol: Optional symbol associated with the evaluated state.

        Returns:
            Risk-limit states for every enabled configured limit.

        Raises:
            ValueError: If market price, daily loss, or symbol is invalid.
        """
        if market_price <= Decimal("0"):
            raise ValueError("market_price must be greater than zero")

        if daily_loss < Decimal("0"):
            raise ValueError("daily_loss must not be negative")

        if symbol is not None and not symbol.strip():
            raise ValueError("symbol must not be blank")

        states: list[RiskLimitState] = []

        if self._config.max_position is not None:
            states.append(
                self._evaluate_limit(
                    limit_type=RiskLimitType.MAX_POSITION,
                    threshold=Decimal(self._config.max_position),
                    current_value=Decimal(abs(snapshot.position)),
                    symbol=symbol,
                )
            )

        if self._config.max_position_value is not None:
            position_value = calculate_position_value(
                position=snapshot.position,
                market_price=market_price,
            )

            states.append(
                self._evaluate_limit(
                    limit_type=RiskLimitType.MAX_POSITION_VALUE,
                    threshold=self._config.max_position_value,
                    current_value=abs(Decimal(position_value)),
                    symbol=symbol,
                )
            )

        if self._config.max_drawdown is not None:
            states.append(
                self._evaluate_limit(
                    limit_type=RiskLimitType.MAX_DRAWDOWN,
                    threshold=self._config.max_drawdown,
                    current_value=snapshot.drawdown,
                    symbol=symbol,
                )
            )

        if self._config.max_daily_loss is not None:
            states.append(
                self._evaluate_limit(
                    limit_type=RiskLimitType.MAX_DAILY_LOSS,
                    threshold=self._config.max_daily_loss,
                    current_value=daily_loss,
                    symbol=symbol,
                )
            )

        return tuple(states)

    def _evaluate_limit(
        self,
        *,
        limit_type: RiskLimitType,
        threshold: Decimal,
        current_value: Decimal,
        symbol: str | None,
    ) -> RiskLimitState:
        """Evaluate one risk limit and return its current state."""
        warning_threshold = threshold * self._config.warning_ratio

        limit = RiskLimit(
            limit_type=limit_type,
            threshold=threshold,
            warning_threshold=warning_threshold,
            symbol=symbol,
        )

        if current_value >= threshold:
            status = RiskLimitStatus.BREACHED
        elif current_value >= warning_threshold:
            status = RiskLimitStatus.WARNING
        else:
            status = RiskLimitStatus.OK

        return RiskLimitState(
            limit=limit,
            current_value=current_value,
            status=status,
        )


__all__ = [
    "RiskLimitEvaluator",
]
