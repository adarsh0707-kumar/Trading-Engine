"""Domain models for risk-limit events."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from decimal import Decimal
from typing import Any

from analytics.models.risk_limit import (
    RiskLimitState,
    RiskLimitStatus,
    RiskLimitType,
)


class RiskEventType(str):
    """Risk-event categories emitted by the analytics risk layer."""

    LIMIT_WARNING = "RISK_LIMIT_WARNING"
    LIMIT_BREACHED = "RISK_LIMIT_BREACHED"
    LIMIT_RECOVERED = "RISK_LIMIT_RECOVERED"


@dataclass(frozen=True, slots=True)
class RiskEvent:
    """Immutable event describing a risk-limit state transition."""

    event_id: str
    event_type: str
    symbol: str | None
    limit_type: RiskLimitType
    status: RiskLimitStatus
    threshold: Decimal
    warning_threshold: Decimal
    current_value: Decimal
    timestamp: datetime

    def __post_init__(self) -> None:
        """Validate the risk event."""

        if not self.event_id:
            raise ValueError("event_id must not be empty")

        if self.event_type not in {
            RiskEventType.LIMIT_WARNING,
            RiskEventType.LIMIT_BREACHED,
            RiskEventType.LIMIT_RECOVERED,
        }:
            raise ValueError("unsupported risk event type")

        if self.threshold <= Decimal("0"):
            raise ValueError("threshold must be greater than zero")

        if self.warning_threshold <= Decimal("0"):
            raise ValueError("warning_threshold must be greater than zero")

        if self.warning_threshold >= self.threshold:
            raise ValueError(
                "warning_threshold must be less than threshold"
            )

        if self.current_value < Decimal("0"):
            raise ValueError("current_value must not be negative")

        expected_status = {
            RiskEventType.LIMIT_WARNING: RiskLimitStatus.WARNING,
            RiskEventType.LIMIT_BREACHED: RiskLimitStatus.BREACHED,
            RiskEventType.LIMIT_RECOVERED: RiskLimitStatus.OK,
        }[self.event_type]
        if self.status != expected_status:
            raise ValueError(
                f"{self.event_type} events must have {expected_status.value.upper()} status"
            )

        if self.symbol is not None and not self.symbol.strip():
            raise ValueError("symbol must not be blank")

    @classmethod
    def from_state(
        cls,
        *,
        event_id: str,
        state: RiskLimitState,
        timestamp: datetime,
    ) -> "RiskEvent":
        """Create a risk event from an evaluated risk-limit state."""

        event_type = {
            RiskLimitStatus.WARNING: RiskEventType.LIMIT_WARNING,
            RiskLimitStatus.BREACHED: RiskEventType.LIMIT_BREACHED,
            RiskLimitStatus.OK: RiskEventType.LIMIT_RECOVERED,
        }[state.status]

        return cls(
            event_id=event_id,
            event_type=event_type,
            symbol=state.limit.symbol,
            limit_type=state.limit.limit_type,
            status=state.status,
            threshold=state.limit.threshold,
            warning_threshold=state.limit.warning_threshold,
            current_value=state.current_value,
            timestamp=timestamp,
        )

    def to_dict(self) -> dict[str, Any]:
        """Convert the risk event into a JSON-friendly dictionary."""

        return {
            "event_id": self.event_id,
            "event_type": self.event_type,
            "symbol": self.symbol,
            "limit_type": self.limit_type.value,
            "status": self.status.value,
            "threshold": str(self.threshold),
            "warning_threshold": str(self.warning_threshold),
            "current_value": str(self.current_value),
            "timestamp": self.timestamp.isoformat(),
        }


__all__ = [
    "RiskEvent",
    "RiskEventType",
]
