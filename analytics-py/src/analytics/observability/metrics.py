"""In-memory metrics for persistence operations."""

from __future__ import annotations

from dataclasses import dataclass
from threading import Lock


@dataclass(frozen=True, slots=True)
class PersistenceMetricsSnapshot:
    """Immutable snapshot of persistence metrics."""

    success_count: int
    failure_count: int
    total_duration_seconds: float

    @property
    def operation_count(self) -> int:
        """Return the total number of completed persistence operations."""
        return self.success_count + self.failure_count

    @property
    def average_duration_seconds(self) -> float:
        """Return average duration across completed operations."""
        if self.operation_count == 0:
            return 0.0

        return self.total_duration_seconds / self.operation_count


class PersistenceMetrics:
    """Thread-safe in-memory metrics for persistence operations."""

    def __init__(self) -> None:
        self._lock = Lock()
        self._success_count = 0
        self._failure_count = 0
        self._total_duration_seconds = 0.0

    def record_success(self, duration_seconds: float) -> None:
        """Record a successful persistence operation."""
        self._record(
            success=True,
            duration_seconds=duration_seconds,
        )

    def record_failure(self, duration_seconds: float) -> None:
        """Record a failed persistence operation."""
        self._record(
            success=False,
            duration_seconds=duration_seconds,
        )

    def snapshot(self) -> PersistenceMetricsSnapshot:
        """Return a consistent immutable metrics snapshot."""
        with self._lock:
            return PersistenceMetricsSnapshot(
                success_count=self._success_count,
                failure_count=self._failure_count,
                total_duration_seconds=self._total_duration_seconds,
            )

    def reset(self) -> None:
        """Reset all persistence metrics."""
        with self._lock:
            self._success_count = 0
            self._failure_count = 0
            self._total_duration_seconds = 0.0

    def _record(
        self,
        *,
        success: bool,
        duration_seconds: float,
    ) -> None:
        if not isinstance(duration_seconds, (int, float)):
            raise TypeError("duration_seconds must be numeric")

        if duration_seconds < 0:
            raise ValueError("duration_seconds must not be negative")

        with self._lock:
            if success:
                self._success_count += 1
            else:
                self._failure_count += 1

            self._total_duration_seconds += float(duration_seconds)


__all__ = [
    "PersistenceMetrics",
    "PersistenceMetricsSnapshot",
]
