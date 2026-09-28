"""Thread-safe service health state for the analytics service."""

from __future__ import annotations

from dataclasses import dataclass
from threading import Lock


@dataclass(frozen=True, slots=True)
class ServiceHealthSnapshot:
    """Immutable snapshot of analytics service health."""

    live: bool
    ready: bool
    engine_connected: bool
    messages_received: int
    last_message_timestamp: float | None


class ServiceHealthMetrics:
    """Track liveness, readiness, and upstream connection health."""

    def __init__(self) -> None:
        self._lock = Lock()
        self._live = False
        self._ready = False
        self._engine_connected = False
        self._messages_received = 0
        self._last_message_timestamp: float | None = None

    def mark_started(self) -> None:
        """Mark the service live but not ready until the engine connects."""
        with self._lock:
            self._live = True
            self._ready = False

    def mark_stopped(self) -> None:
        """Mark the service stopped and unavailable."""
        with self._lock:
            self._live = False
            self._ready = False
            self._engine_connected = False

    def mark_engine_connected(self) -> None:
        """Mark the trading-engine dependency as connected and ready."""
        with self._lock:
            self._engine_connected = True
            self._ready = self._live

    def mark_engine_disconnected(self) -> None:
        """Mark the trading-engine dependency as disconnected."""
        with self._lock:
            self._engine_connected = False
            self._ready = False

    def record_message(self, timestamp: float) -> None:
        """Record receipt of one inbound message."""
        if not isinstance(timestamp, (int, float)):
            raise TypeError("timestamp must be numeric")
        with self._lock:
            self._messages_received += 1
            self._last_message_timestamp = float(timestamp)

    def snapshot(self) -> ServiceHealthSnapshot:
        """Return a consistent immutable health snapshot."""
        with self._lock:
            return ServiceHealthSnapshot(
                live=self._live,
                ready=self._ready,
                engine_connected=self._engine_connected,
                messages_received=self._messages_received,
                last_message_timestamp=self._last_message_timestamp,
            )

    def reset(self) -> None:
        """Reset health state to its initial stopped condition."""
        with self._lock:
            self._live = False
            self._ready = False
            self._engine_connected = False
            self._messages_received = 0
            self._last_message_timestamp = None


__all__ = ["ServiceHealthMetrics", "ServiceHealthSnapshot"]
