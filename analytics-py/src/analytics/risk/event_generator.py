"""Risk-event generation from evaluated risk-limit states."""

from __future__ import annotations

from datetime import datetime

from analytics.models.risk_event import RiskEvent
from analytics.models.risk_limit import RiskLimitState, RiskLimitStatus


class RiskEventGenerator:
    """Generate risk events from warning or breached limit states."""

    def __init__(self, *, event_prefix: str = "risk") -> None:
        """Initialize the event generator."""

        if not event_prefix.strip():
            raise ValueError("event_prefix must not be blank")

        self._event_prefix = event_prefix
        self._sequence = 0

    def generate(
        self,
        *,
        states: tuple[RiskLimitState, ...],
        timestamp: datetime,
    ) -> tuple[RiskEvent, ...]:
        """Generate events for WARNING and BREACHED states.

        OK states do not produce events.
        """

        events: list[RiskEvent] = []

        for state in states:
            if state.status not in {
                RiskLimitStatus.WARNING,
                RiskLimitStatus.BREACHED,
            }:
                continue

            self._sequence += 1

            event_id = (
                f"{self._event_prefix}-"
                f"{state.limit.limit_type.value}-"
                f"{self._sequence}"
            )

            events.append(
                RiskEvent.from_state(
                    event_id=event_id,
                    state=state,
                    timestamp=timestamp,
                )
            )

        return tuple(events)


__all__ = [
    "RiskEventGenerator",
]
