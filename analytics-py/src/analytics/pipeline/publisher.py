"""Analytics result publisher."""

from __future__ import annotations

import logging
import time

from analytics.integration.gateway_message import (
    serialize_analytics_update,
    serialize_risk_event,
)
from analytics.models import AnalyticsResult, RiskEvent

logger = logging.getLogger(__name__)


class AnalyticsPublisher:
    """Publish analytics and risk results to an injected sink."""

    def __init__(
        self,
        sink,
        *,
        retry_attempts: int = 0,
        retry_delay: float = 0.0,
    ) -> None:
        if not callable(sink):
            raise TypeError("sink must be callable")
        if (
            isinstance(retry_attempts, bool)
            or not isinstance(retry_attempts, int)
            or retry_attempts < 0
        ):
            raise ValueError(
                "retry_attempts must be an integer greater than or equal to 0"
            )
        if retry_delay < 0:
            raise ValueError("retry_delay must be greater than or equal to 0")

        self._sink = sink
        self._retry_attempts = retry_attempts
        self._retry_delay = retry_delay

    def _publish_payload(
        self,
        payload: str,
        *,
        event_id: str,
        symbol: str | None,
    ) -> None:
        attempts = self._retry_attempts + 1

        for attempt in range(attempts):
            try:
                self._sink(payload)
                return
            except Exception as exc:
                if attempt >= self._retry_attempts:
                    logger.error(
                        "analytics_publish_failed event_id=%s symbol=%s "
                        "attempt=%d total_attempts=%d error=%s",
                        event_id,
                        symbol,
                        attempt + 1,
                        attempts,
                        exc,
                    )
                    raise

                logger.warning(
                    "analytics_publish_retry event_id=%s symbol=%s "
                    "attempt=%d total_attempts=%d error=%s",
                    event_id,
                    symbol,
                    attempt + 1,
                    attempts,
                    exc,
                )

                if self._retry_delay:
                    time.sleep(self._retry_delay)

    def publish(self, result: AnalyticsResult) -> None:
        """Serialize and publish one analytics result."""

        if not isinstance(result, AnalyticsResult):
            raise TypeError("result must be an AnalyticsResult")

        payload = serialize_analytics_update(result)

        self._publish_payload(
            payload,
            event_id=result.event_id,
            symbol=result.symbol,
        )

    def publish_risk_event(self, event: RiskEvent) -> None:
        """Serialize and publish one risk event."""

        if not isinstance(event, RiskEvent):
            raise TypeError("event must be a RiskEvent")

        payload = serialize_risk_event(event)

        self._publish_payload(
            payload,
            event_id=event.event_id,
            symbol=event.symbol,
        )


__all__ = ["AnalyticsPublisher"]
