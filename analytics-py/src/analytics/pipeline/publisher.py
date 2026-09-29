"""Analytics result publisher."""

from __future__ import annotations

import json
import time
from collections.abc import Callable
from typing import Any

from analytics.models import AnalyticsResult


class AnalyticsPublisher:
    """Publish AnalyticsResult objects to an injected sink.

    The publisher is transport-independent. The caller decides whether the
    serialized message is sent to a socket, queue, file, or another system.
    """

    def __init__(
        self,
        sink: Callable[[str], Any],
        *,
        retry_attempts: int = 0,
        retry_delay: float = 0.0,
    ) -> None:
        if not callable(sink):
            raise TypeError("sink must be callable")
        if isinstance(retry_attempts, bool) or not isinstance(retry_attempts, int) or retry_attempts < 0:
            raise ValueError("retry_attempts must be an integer greater than or equal to 0")
        if retry_delay < 0:
            raise ValueError("retry_delay must be greater than or equal to 0")

        self._sink = sink
        self._retry_attempts = retry_attempts
        self._retry_delay = retry_delay

    def publish(self, result: AnalyticsResult) -> None:
        """Serialize and publish one analytics result."""

        if not isinstance(result, AnalyticsResult):
            raise TypeError("result must be an AnalyticsResult")

        payload = json.dumps(
            result.to_dict(),
            separators=(",", ":"),
            sort_keys=True,
        )

        attempts = self._retry_attempts + 1
        for attempt in range(attempts):
            try:
                self._sink(payload)
                return
            except Exception:
                if attempt >= self._retry_attempts:
                    raise
                if self._retry_delay:
                    time.sleep(self._retry_delay)


__all__ = ["AnalyticsPublisher"]
