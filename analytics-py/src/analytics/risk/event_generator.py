"""Risk-event generation from evaluated risk-limit states."""

from __future__ import annotations

from datetime import date, datetime

from analytics.models.risk_event import RiskEvent
from analytics.models.risk_limit import RiskLimitState, RiskLimitStatus, RiskLimitType


class RiskEventGenerator:
    """Generate risk events and report transitions back to an OK state."""

    def __init__(self, *, event_prefix: str = "risk") -> None:
        """Initialize the event generator."""

        if not event_prefix.strip():
            raise ValueError("event_prefix must not be blank")

        self._event_prefix = event_prefix
        self._sequence = 0
        self._previous_alert_status: dict[
            tuple[str | None, RiskLimitType, date | None], RiskLimitStatus
        ] = {}

    def generate(
        self,
        *,
        states: tuple[RiskLimitState, ...],
        timestamp: datetime,
    ) -> tuple[RiskEvent, ...]:
        """Generate alert events and recovery events for previously active alerts.

        WARNING and BREACHED states continue to emit events on every evaluation.
        An OK state emits a recovery event only when the same symbol/limit was
        previously WARNING or BREACHED during the same risk period. Daily-loss
        state is scoped to the timestamp's date because its baseline resets at
        the start of each trading day.
        """

        current_date = timestamp.date()
        self._previous_alert_status = {
            key: status
            for key, status in self._previous_alert_status.items()
            if key[1] != RiskLimitType.MAX_DAILY_LOSS or key[2] == current_date
        }

        events: list[RiskEvent] = []

        for state in states:
            risk_date = (
                current_date
                if state.limit.limit_type == RiskLimitType.MAX_DAILY_LOSS
                else None
            )
            key = (state.limit.symbol, state.limit.limit_type, risk_date)

            if state.status in {
                RiskLimitStatus.WARNING,
                RiskLimitStatus.BREACHED,
            }:
                self._previous_alert_status[key] = state.status
            elif state.status == RiskLimitStatus.OK:
                previous_status = self._previous_alert_status.pop(key, None)
                if previous_status is None:
                    continue
            else:
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
