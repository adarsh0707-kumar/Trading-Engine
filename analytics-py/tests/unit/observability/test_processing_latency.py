"""Tests for analytics processing latency metrics."""

from __future__ import annotations

import threading

import pytest

from analytics.observability import (
    ProcessingLatencyMetrics,
    ProcessingLatencySnapshot,
)


def test_new_latency_metrics_are_empty() -> None:
    metrics = ProcessingLatencyMetrics()

    snapshot = metrics.snapshot()

    assert snapshot == ProcessingLatencySnapshot(
        sample_count=0,
        total_duration_seconds=0.0,
        min_duration_seconds=None,
        max_duration_seconds=None,
        p50_duration_seconds=None,
        p95_duration_seconds=None,
        p99_duration_seconds=None,
    )
    assert snapshot.average_duration_seconds == 0.0


def test_snapshot_reports_latency_aggregates() -> None:
    metrics = ProcessingLatencyMetrics()

    for duration in (0.100, 0.200, 0.300):
        metrics.record(duration)

    snapshot = metrics.snapshot()

    assert snapshot.sample_count == 3
    assert snapshot.total_duration_seconds == pytest.approx(0.600)
    assert snapshot.average_duration_seconds == pytest.approx(0.200)
    assert snapshot.min_duration_seconds == pytest.approx(0.100)
    assert snapshot.max_duration_seconds == pytest.approx(0.300)
    assert snapshot.p50_duration_seconds == pytest.approx(0.200)
    assert snapshot.p95_duration_seconds == pytest.approx(0.290)
    assert snapshot.p99_duration_seconds == pytest.approx(0.298)


def test_percentiles_are_interpolated() -> None:
    metrics = ProcessingLatencyMetrics()

    for duration in (0.1, 0.2, 0.3, 1.0, 2.0):
        metrics.record(duration)

    snapshot = metrics.snapshot()

    assert snapshot.p50_duration_seconds == pytest.approx(0.3)
    assert snapshot.p95_duration_seconds == pytest.approx(1.8)
    assert snapshot.p99_duration_seconds == pytest.approx(1.96)


def test_single_latency_sample_is_used_for_all_percentiles() -> None:
    metrics = ProcessingLatencyMetrics()

    metrics.record(0.125)

    snapshot = metrics.snapshot()

    assert snapshot.sample_count == 1
    assert snapshot.min_duration_seconds == pytest.approx(0.125)
    assert snapshot.max_duration_seconds == pytest.approx(0.125)
    assert snapshot.p50_duration_seconds == pytest.approx(0.125)
    assert snapshot.p95_duration_seconds == pytest.approx(0.125)
    assert snapshot.p99_duration_seconds == pytest.approx(0.125)


def test_snapshot_is_immutable() -> None:
    metrics = ProcessingLatencyMetrics()

    snapshot = metrics.snapshot()

    with pytest.raises(AttributeError):
        snapshot.sample_count = 10  # type: ignore[misc]


def test_negative_duration_is_rejected() -> None:
    metrics = ProcessingLatencyMetrics()

    with pytest.raises(
        ValueError,
        match="duration_seconds must not be negative",
    ):
        metrics.record(-0.1)


def test_non_numeric_duration_is_rejected() -> None:
    metrics = ProcessingLatencyMetrics()

    with pytest.raises(
        TypeError,
        match="duration_seconds must be numeric",
    ):
        metrics.record("0.1")  # type: ignore[arg-type]


def test_reset_clears_latency_samples() -> None:
    metrics = ProcessingLatencyMetrics()

    metrics.record(0.100)
    metrics.record(0.200)

    metrics.reset()

    snapshot = metrics.snapshot()

    assert snapshot.sample_count == 0
    assert snapshot.total_duration_seconds == 0.0
    assert snapshot.min_duration_seconds is None
    assert snapshot.max_duration_seconds is None
    assert snapshot.p50_duration_seconds is None
    assert snapshot.p95_duration_seconds is None
    assert snapshot.p99_duration_seconds is None


def test_latency_metrics_are_thread_safe() -> None:
    metrics = ProcessingLatencyMetrics()

    def record_operations() -> None:
        for _ in range(100):
            metrics.record(0.001)
            metrics.record(0.002)

    threads = [
        threading.Thread(target=record_operations)
        for _ in range(5)
    ]

    for thread in threads:
        thread.start()

    for thread in threads:
        thread.join()

    snapshot = metrics.snapshot()

    assert snapshot.sample_count == 1000
    assert snapshot.total_duration_seconds == pytest.approx(1.5)
    assert snapshot.average_duration_seconds == pytest.approx(0.0015)
    assert snapshot.min_duration_seconds == pytest.approx(0.001)
    assert snapshot.max_duration_seconds == pytest.approx(0.002)
