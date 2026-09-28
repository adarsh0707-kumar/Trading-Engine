"""Backpressure observability metrics."""

from __future__ import annotations

from dataclasses import dataclass
from threading import Lock


@dataclass(frozen=True, slots=True)
class BackpressureMetricsSnapshot:
    """Immutable backpressure metrics snapshot."""

    queue_depth: int
    enqueued_count: int
    rejected_count: int


class BackpressureMetrics:
    """Thread-safe counters for bounded inbound message handling."""

    def __init__(self) -> None:
        self._lock = Lock()
        self._queue_depth = 0
        self._enqueued_count = 0
        self._rejected_count = 0

    def set_queue_depth(self, depth: int) -> None:
        if depth < 0:
            raise ValueError("queue depth must not be negative")
        with self._lock:
            self._queue_depth = depth

    def record_enqueued(self) -> None:
        with self._lock:
            self._enqueued_count += 1

    def record_rejected(self) -> None:
        with self._lock:
            self._rejected_count += 1

    def snapshot(self) -> BackpressureMetricsSnapshot:
        with self._lock:
            return BackpressureMetricsSnapshot(
                queue_depth=self._queue_depth,
                enqueued_count=self._enqueued_count,
                rejected_count=self._rejected_count,
            )

    def reset(self) -> None:
        with self._lock:
            self._queue_depth = 0
            self._enqueued_count = 0
            self._rejected_count = 0
