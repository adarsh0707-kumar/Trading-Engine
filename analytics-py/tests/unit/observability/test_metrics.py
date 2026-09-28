"""Tests for persistence observability metrics."""

from __future__ import annotations

import threading

import pytest

from analytics.observability import (
    PersistenceMetrics,
    PersistenceMetricsSnapshot,
)


def test_new_metrics_are_empty() -> None:
    metrics = PersistenceMetrics()

    snapshot = metrics.snapshot()

    assert snapshot == PersistenceMetricsSnapshot(
        success_count=0,
        failure_count=0,
        total_duration_seconds=0.0,
    )
    assert snapshot.operation_count == 0
    assert snapshot.average_duration_seconds == 0.0


def test_record_success() -> None:
    metrics = PersistenceMetrics()

    metrics.record_success(0.125)

    snapshot = metrics.snapshot()

    assert snapshot.success_count == 1
    assert snapshot.failure_count == 0
    assert snapshot.total_duration_seconds == pytest.approx(0.125)
    assert snapshot.operation_count == 1
    assert snapshot.average_duration_seconds == pytest.approx(0.125)


def test_record_failure() -> None:
    metrics = PersistenceMetrics()

    metrics.record_failure(0.250)

    snapshot = metrics.snapshot()

    assert snapshot.success_count == 0
    assert snapshot.failure_count == 1
    assert snapshot.total_duration_seconds == pytest.approx(0.250)
    assert snapshot.operation_count == 1
    assert snapshot.average_duration_seconds == pytest.approx(0.250)


def test_snapshot_accumulates_successes_and_failures() -> None:
    metrics = PersistenceMetrics()

    metrics.record_success(0.100)
    metrics.record_failure(0.200)
    metrics.record_success(0.300)

    snapshot = metrics.snapshot()

    assert snapshot.success_count == 2
    assert snapshot.failure_count == 1
    assert snapshot.total_duration_seconds == pytest.approx(0.600)
    assert snapshot.operation_count == 3
    assert snapshot.average_duration_seconds == pytest.approx(0.200)


def test_snapshot_is_immutable() -> None:
    metrics = PersistenceMetrics()

    snapshot = metrics.snapshot()

    with pytest.raises(AttributeError):
        snapshot.success_count = 10  # type: ignore[misc]


def test_negative_duration_is_rejected() -> None:
    metrics = PersistenceMetrics()

    with pytest.raises(
        ValueError,
        match="duration_seconds must not be negative",
    ):
        metrics.record_success(-0.1)


def test_non_numeric_duration_is_rejected() -> None:
    metrics = PersistenceMetrics()

    with pytest.raises(
        TypeError,
        match="duration_seconds must be numeric",
    ):
        metrics.record_success("0.1")  # type: ignore[arg-type]


def test_reset_clears_metrics() -> None:
    metrics = PersistenceMetrics()

    metrics.record_success(0.100)
    metrics.record_failure(0.200)

    metrics.reset()

    snapshot = metrics.snapshot()

    assert snapshot.success_count == 0
    assert snapshot.failure_count == 0
    assert snapshot.total_duration_seconds == 0.0


def test_metrics_are_thread_safe() -> None:
    metrics = PersistenceMetrics()

    def record_operations() -> None:
        for _ in range(100):
            metrics.record_success(0.001)
            metrics.record_failure(0.002)

    threads = [
        threading.Thread(target=record_operations)
        for _ in range(5)
    ]

    for thread in threads:
        thread.start()

    for thread in threads:
        thread.join()

    snapshot = metrics.snapshot()

    assert snapshot.success_count == 500
    assert snapshot.failure_count == 500
    assert snapshot.operation_count == 1000
    assert snapshot.total_duration_seconds == pytest.approx(1.5)
