"""Tests for service error counters."""

import threading

import pytest

from analytics.observability import ErrorMetrics, ErrorMetricsSnapshot


def test_new_metrics_are_empty() -> None:
    metrics = ErrorMetrics()
    assert metrics.snapshot() == ErrorMetricsSnapshot(0, 0, 0, 0, 0)
    assert metrics.snapshot().total_error_count == 0


def test_error_categories_accumulate() -> None:
    metrics = ErrorMetrics()
    metrics.record_parse_error()
    metrics.record_processing_error()
    metrics.record_processing_error()
    metrics.record_persistence_error()
    metrics.record_publish_error()
    metrics.record_unknown_error()

    snapshot = metrics.snapshot()
    assert snapshot.parse_error_count == 1
    assert snapshot.processing_error_count == 2
    assert snapshot.persistence_error_count == 1
    assert snapshot.publish_error_count == 1
    assert snapshot.unknown_error_count == 1
    assert snapshot.total_error_count == 6


def test_snapshot_is_immutable() -> None:
    snapshot = ErrorMetrics().snapshot()
    with pytest.raises(AttributeError):
        snapshot.parse_error_count = 10  # type: ignore[misc]


def test_reset_clears_all_error_counters() -> None:
    metrics = ErrorMetrics()
    metrics.record_parse_error()
    metrics.record_processing_error()
    metrics.record_persistence_error()
    metrics.record_publish_error()
    metrics.record_unknown_error()

    metrics.reset()

    assert metrics.snapshot() == ErrorMetricsSnapshot(0, 0, 0, 0, 0)


def test_error_metrics_are_thread_safe() -> None:
    metrics = ErrorMetrics()

    def record() -> None:
        for _ in range(100):
            metrics.record_parse_error()
            metrics.record_processing_error()
            metrics.record_persistence_error()
            metrics.record_publish_error()
            metrics.record_unknown_error()

    threads = [threading.Thread(target=record) for _ in range(5)]
    for thread in threads:
        thread.start()
    for thread in threads:
        thread.join()

    snapshot = metrics.snapshot()
    assert snapshot.parse_error_count == 500
    assert snapshot.processing_error_count == 500
    assert snapshot.persistence_error_count == 500
    assert snapshot.publish_error_count == 500
    assert snapshot.unknown_error_count == 500
