"""In-memory metrics for analytics service operations."""

from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal
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


@dataclass(frozen=True, slots=True)
class ServiceMetricsSnapshot:
    """Immutable snapshot of analytics service metrics."""

    processed_trade_count: int
    processing_failure_count: int
    parse_error_count: int
    ignored_event_count: int
    published_analytics_count: int
    total_processing_duration_seconds: float

    @property
    def trade_attempt_count(self) -> int:
        """Return the total number of trade pipeline attempts."""
        return (
            self.processed_trade_count
            + self.processing_failure_count
        )

    @property
    def average_processing_duration_seconds(self) -> float:
        """Return average duration across trade pipeline attempts."""
        if self.trade_attempt_count == 0:
            return 0.0

        return (
            self.total_processing_duration_seconds
            / self.trade_attempt_count
        )


class ServiceMetrics:
    """Thread-safe in-memory metrics for the analytics service."""

    def __init__(self) -> None:
        self._lock = Lock()
        self._processed_trade_count = 0
        self._processing_failure_count = 0
        self._parse_error_count = 0
        self._ignored_event_count = 0
        self._published_analytics_count = 0
        self._total_processing_duration_seconds = 0.0

    def record_trade_success(self, duration_seconds: float) -> None:
        """Record a successfully completed trade pipeline."""
        self._record_trade(
            success=True,
            duration_seconds=duration_seconds,
        )

    def record_trade_failure(self, duration_seconds: float) -> None:
        """Record a failed trade pipeline."""
        self._record_trade(
            success=False,
            duration_seconds=duration_seconds,
        )

    def record_parse_error(self) -> None:
        """Record an incoming message that failed parsing."""
        with self._lock:
            self._parse_error_count += 1

    def record_ignored_event(self) -> None:
        """Record a valid event ignored by the current pipeline."""
        with self._lock:
            self._ignored_event_count += 1

    def record_published_analytics(self) -> None:
        """Record an analytics result handed to the publisher."""
        with self._lock:
            self._published_analytics_count += 1

    def snapshot(self) -> ServiceMetricsSnapshot:
        """Return a consistent immutable metrics snapshot."""
        with self._lock:
            return ServiceMetricsSnapshot(
                processed_trade_count=self._processed_trade_count,
                processing_failure_count=self._processing_failure_count,
                parse_error_count=self._parse_error_count,
                ignored_event_count=self._ignored_event_count,
                published_analytics_count=self._published_analytics_count,
                total_processing_duration_seconds=(
                    self._total_processing_duration_seconds
                ),
            )

    def reset(self) -> None:
        """Reset all service metrics."""
        with self._lock:
            self._processed_trade_count = 0
            self._processing_failure_count = 0
            self._parse_error_count = 0
            self._ignored_event_count = 0
            self._published_analytics_count = 0
            self._total_processing_duration_seconds = 0.0

    def _record_trade(
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
                self._processed_trade_count += 1
            else:
                self._processing_failure_count += 1

            self._total_processing_duration_seconds += float(
                duration_seconds,
            )


@dataclass(frozen=True, slots=True)
class ErrorMetricsSnapshot:
    """Immutable snapshot of service error counters."""

    parse_error_count: int
    processing_error_count: int
    persistence_error_count: int
    publish_error_count: int
    unknown_error_count: int

    @property
    def total_error_count(self) -> int:
        """Return the total number of recorded errors."""
        return (
            self.parse_error_count
            + self.processing_error_count
            + self.persistence_error_count
            + self.publish_error_count
            + self.unknown_error_count
        )


class ErrorMetrics:
    """Thread-safe counters for errors crossing service boundaries."""

    def __init__(self) -> None:
        self._lock = Lock()
        self._parse_error_count = 0
        self._processing_error_count = 0
        self._persistence_error_count = 0
        self._publish_error_count = 0
        self._unknown_error_count = 0

    def record_parse_error(self) -> None:
        with self._lock:
            self._parse_error_count += 1

    def record_processing_error(self) -> None:
        with self._lock:
            self._processing_error_count += 1

    def record_persistence_error(self) -> None:
        with self._lock:
            self._persistence_error_count += 1

    def record_publish_error(self) -> None:
        with self._lock:
            self._publish_error_count += 1

    def record_unknown_error(self) -> None:
        with self._lock:
            self._unknown_error_count += 1

    def snapshot(self) -> ErrorMetricsSnapshot:
        with self._lock:
            return ErrorMetricsSnapshot(
                parse_error_count=self._parse_error_count,
                processing_error_count=self._processing_error_count,
                persistence_error_count=self._persistence_error_count,
                publish_error_count=self._publish_error_count,
                unknown_error_count=self._unknown_error_count,
            )

    def reset(self) -> None:
        with self._lock:
            self._parse_error_count = 0
            self._processing_error_count = 0
            self._persistence_error_count = 0
            self._publish_error_count = 0
            self._unknown_error_count = 0


@dataclass(frozen=True, slots=True)
class ProcessingLatencySnapshot:
    """Immutable snapshot of analytics processing latency metrics."""

    sample_count: int
    total_duration_seconds: float
    min_duration_seconds: float | None
    max_duration_seconds: float | None
    p50_duration_seconds: float | None
    p95_duration_seconds: float | None
    p99_duration_seconds: float | None

    @property
    def average_duration_seconds(self) -> float:
        """Return average processing latency across recorded samples."""
        if self.sample_count == 0:
            return 0.0

        return self.total_duration_seconds / self.sample_count


class ProcessingLatencyMetrics:
    """Thread-safe in-memory processing latency measurements."""

    def __init__(self) -> None:
        self._lock = Lock()
        self._durations_seconds: list[float] = []

    def record(self, duration_seconds: float) -> None:
        """Record one non-negative processing duration."""
        if not isinstance(duration_seconds, (int, float)):
            raise TypeError("duration_seconds must be numeric")

        if duration_seconds < 0:
            raise ValueError("duration_seconds must not be negative")

        with self._lock:
            self._durations_seconds.append(float(duration_seconds))

    def snapshot(self) -> ProcessingLatencySnapshot:
        """Return latency aggregates and percentile measurements."""
        with self._lock:
            durations = tuple(sorted(self._durations_seconds))

        if not durations:
            return ProcessingLatencySnapshot(
                sample_count=0,
                total_duration_seconds=0.0,
                min_duration_seconds=None,
                max_duration_seconds=None,
                p50_duration_seconds=None,
                p95_duration_seconds=None,
                p99_duration_seconds=None,
            )

        return ProcessingLatencySnapshot(
            sample_count=len(durations),
            total_duration_seconds=sum(durations),
            min_duration_seconds=durations[0],
            max_duration_seconds=durations[-1],
            p50_duration_seconds=self._percentile(durations, 0.50),
            p95_duration_seconds=self._percentile(durations, 0.95),
            p99_duration_seconds=self._percentile(durations, 0.99),
        )

    def reset(self) -> None:
        """Reset all recorded latency samples."""
        with self._lock:
            self._durations_seconds.clear()

    @staticmethod
    def _percentile(durations: tuple[float, ...], percentile: float) -> float:
        """Return a linearly interpolated percentile."""
        if len(durations) == 1:
            return durations[0]

        position = (len(durations) - 1) * percentile
        lower = int(position)
        upper = min(lower + 1, len(durations) - 1)
        weight = position - lower

        return (
            durations[lower]
            + (durations[upper] - durations[lower]) * weight
        )


@dataclass(frozen=True, slots=True)
class TradeThroughputSnapshot:
    """Immutable snapshot of recent trade throughput."""

    trade_count: int
    window_seconds: float
    trades_per_second: float
    total_trade_count: int


class TradeThroughputMetrics:
    """Thread-safe in-memory throughput measurements for processed trades."""

    def __init__(self, *, window_seconds: float = 60.0) -> None:
        if not isinstance(window_seconds, (int, float)):
            raise TypeError("window_seconds must be numeric")

        if window_seconds <= 0:
            raise ValueError("window_seconds must be positive")

        self._lock = Lock()
        self._window_seconds = float(window_seconds)
        self._timestamps: list[float] = []
        self._total_trade_count = 0

    def record_trade(self, timestamp_seconds: float | None = None) -> None:
        """Record one successfully processed trade."""
        if timestamp_seconds is None:
            from time import perf_counter

            timestamp_seconds = perf_counter()

        if not isinstance(timestamp_seconds, (int, float)):
            raise TypeError("timestamp_seconds must be numeric")

        with self._lock:
            self._timestamps.append(float(timestamp_seconds))
            self._total_trade_count += 1
            self._prune(float(timestamp_seconds))

    def snapshot(self, timestamp_seconds: float | None = None) -> TradeThroughputSnapshot:
        """Return throughput for the configured recent time window."""
        if timestamp_seconds is None:
            from time import perf_counter

            timestamp_seconds = perf_counter()

        if not isinstance(timestamp_seconds, (int, float)):
            raise TypeError("timestamp_seconds must be numeric")

        now = float(timestamp_seconds)

        with self._lock:
            self._prune(now)
            count = len(self._timestamps)

        return TradeThroughputSnapshot(
            trade_count=count,
            window_seconds=self._window_seconds,
            trades_per_second=count / self._window_seconds,
            total_trade_count=self._total_trade_count,
        )

    def reset(self) -> None:
        """Reset all throughput measurements."""
        with self._lock:
            self._timestamps.clear()
            self._total_trade_count = 0

    def _prune(self, now: float) -> None:
        """Drop timestamps outside the configured measurement window."""
        cutoff = now - self._window_seconds

        first_valid = 0
        for timestamp in self._timestamps:
            if timestamp >= cutoff:
                break
            first_valid += 1

        if first_valid:
            del self._timestamps[:first_valid]


@dataclass(frozen=True, slots=True)
class RiskMetricsSnapshot:
    """Immutable snapshot of portfolio risk metrics."""

    sample_count: int
    current_position: int
    max_abs_position: int
    current_realized_pnl: Decimal
    current_unrealized_pnl: Decimal
    current_equity: Decimal
    peak_equity: Decimal
    current_drawdown: Decimal
    max_drawdown: Decimal
    warning_event_count: int
    breached_event_count: int


class RiskMetrics:
    """Thread-safe in-memory measurements of portfolio risk state."""

    def __init__(self) -> None:
        self._lock = Lock()
        self._sample_count = 0
        self._current_position = 0
        self._max_abs_position = 0
        self._current_realized_pnl = Decimal("0")
        self._current_unrealized_pnl = Decimal("0")
        self._current_equity = Decimal("0")
        self._peak_equity = Decimal("0")
        self._current_drawdown = Decimal("0")
        self._max_drawdown = Decimal("0")
        self._warning_event_count = 0
        self._breached_event_count = 0

    def record_snapshot(
        self,
        *,
        position: int,
        realized_pnl: Decimal,
        unrealized_pnl: Decimal,
        equity: Decimal,
        peak_equity: Decimal,
        drawdown: Decimal,
    ) -> None:
        """Record one portfolio risk snapshot."""
        values = (
            realized_pnl,
            unrealized_pnl,
            equity,
            peak_equity,
            drawdown,
        )
        if not all(isinstance(value, Decimal) for value in values):
            raise TypeError("risk values must be Decimal")
        if not isinstance(position, int):
            raise TypeError("position must be an integer")
        if drawdown < 0:
            raise ValueError("drawdown must not be negative")

        with self._lock:
            self._sample_count += 1
            self._current_position = position
            self._max_abs_position = max(
                self._max_abs_position,
                abs(position),
            )
            self._current_realized_pnl = realized_pnl
            self._current_unrealized_pnl = unrealized_pnl
            self._current_equity = equity
            self._peak_equity = peak_equity
            self._current_drawdown = drawdown
            self._max_drawdown = max(self._max_drawdown, drawdown)

    def record_warning_event(self) -> None:
        """Record one risk-limit warning event."""
        with self._lock:
            self._warning_event_count += 1

    def record_breached_event(self) -> None:
        """Record one risk-limit breach event."""
        with self._lock:
            self._breached_event_count += 1

    def snapshot(self) -> RiskMetricsSnapshot:
        """Return a consistent immutable risk metrics snapshot."""
        with self._lock:
            return RiskMetricsSnapshot(
                sample_count=self._sample_count,
                current_position=self._current_position,
                max_abs_position=self._max_abs_position,
                current_realized_pnl=self._current_realized_pnl,
                current_unrealized_pnl=self._current_unrealized_pnl,
                current_equity=self._current_equity,
                peak_equity=self._peak_equity,
                current_drawdown=self._current_drawdown,
                max_drawdown=self._max_drawdown,
                warning_event_count=self._warning_event_count,
                breached_event_count=self._breached_event_count,
            )

    def reset(self) -> None:
        """Reset all recorded risk metrics."""
        with self._lock:
            self._sample_count = 0
            self._current_position = 0
            self._max_abs_position = 0
            self._current_realized_pnl = Decimal("0")
            self._current_unrealized_pnl = Decimal("0")
            self._current_equity = Decimal("0")
            self._peak_equity = Decimal("0")
            self._current_drawdown = Decimal("0")
            self._max_drawdown = Decimal("0")
            self._warning_event_count = 0
            self._breached_event_count = 0


__all__ = [
    "ErrorMetrics",
    "ErrorMetricsSnapshot",
    "PersistenceMetrics",
    "PersistenceMetricsSnapshot",
    "ProcessingLatencyMetrics",
    "ProcessingLatencySnapshot",
    "ServiceMetrics",
    "TradeThroughputMetrics",
    "TradeThroughputSnapshot",
    "RiskMetrics",
    "RiskMetricsSnapshot",
    "ServiceMetricsSnapshot",
]
