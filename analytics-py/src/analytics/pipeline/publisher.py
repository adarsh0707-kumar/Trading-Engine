"""Analytics result publisher."""

from __future__ import annotations

import json
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
    ) -> None:
        if not callable(sink):
            raise TypeError("sink must be callable")

        self._sink = sink

    def publish(self, result: AnalyticsResult) -> None:
        """Serialize and publish one analytics result."""

        if not isinstance(result, AnalyticsResult):
            raise TypeError("result must be an AnalyticsResult")

        payload = json.dumps(
            result.to_dict(),
            separators=(",", ":"),
            sort_keys=True,
        )

        self._sink(payload)


__all__ = ["AnalyticsPublisher"]
