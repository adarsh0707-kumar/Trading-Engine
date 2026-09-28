"""Tests for analytics service metrics."""

from __future__ import annotations

import threading

import pytest

from analytics.observability import (
    ServiceMetrics,
    ServiceMetricsSnapshot,
)


def test_new_metrics_are_empty() -> None:
    metrics = ServiceMetrics()

    snapshot = metrics.snapshot()

    assert snapshot == ServiceMetricsSnapshot(
        processed_trade_count=0,
        processing_failure_count=0,
        parse_error_count=0,
        ignored_event_count=0,
        published_analytics_count=0,
        total_processing_duration_seconds=0.0,
    )
    assert snapshot.trade_attempt_count == 0
    assert snapshot.average_processing_duration_seconds == 0.0


def test_record_trade_success() -> None:
    metrics = ServiceMetrics()

    metrics.record_trade_success(0.125)

    snapshot = metrics.snapshot()

    assert snapshot.processed_trade_count == 1
    assert snapshot.processing_failure_count == 0
    assert snapshot.total_processing_duration_seconds == pytest.approx(
        0.125,
    )
    assert snapshot.trade_attempt_count == 1
    assert snapshot.average_processing_duration_seconds == pytest.approx(
        0.125,
    )


def test_record_trade_failure() -> None:
    metrics = ServiceMetrics()

    metrics.record_trade_failure(0.250)

    snapshot = metrics.snapshot()

    assert snapshot.processed_trade_count == 0
    assert snapshot.processing_failure_count == 1
    assert snapshot.total_processing_duration_seconds == pytest.approx(
        0.250,
    )
    assert snapshot.trade_attempt_count == 1
    assert snapshot.average_processing_duration_seconds == pytest.approx(
        0.250,
    )


def test_record_message_categories() -> None:
    metrics = ServiceMetrics()

    metrics.record_parse_error()
    metrics.record_parse_error()
    metrics.record_ignored_event()
    metrics.record_published_analytics()
    metrics.record_published_analytics()

    snapshot = metrics.snapshot()

    assert snapshot.parse_error_count == 2
    assert snapshot.ignored_event_count == 1
    assert snapshot.published_analytics_count == 2


def test_snapshot_accumulates_trade_metrics() -> None:
    metrics = ServiceMetrics()

    metrics.record_trade_success(0.100)
    metrics.record_trade_failure(0.200)
    metrics.record_trade_success(0.300)

    snapshot = metrics.snapshot()

    assert snapshot.processed_trade_count == 2
    assert snapshot.processing_failure_count == 1
    assert snapshot.trade_attempt_count == 3
    assert snapshot.total_processing_duration_seconds == pytest.approx(
        0.600,
    )
    assert snapshot.average_processing_duration_seconds == pytest.approx(
        0.200,
    )


def test_snapshot_is_immutable() -> None:
    metrics = ServiceMetrics()

    snapshot = metrics.snapshot()

    with pytest.raises(AttributeError):
        snapshot.processed_trade_count = 10  # type: ignore[misc]


def test_negative_duration_is_rejected() -> None:
    metrics = ServiceMetrics()

    with pytest.raises(
        ValueError,
        match="duration_seconds must not be negative",
    ):
        metrics.record_trade_success(-0.1)


def test_non_numeric_duration_is_rejected() -> None:
    metrics = ServiceMetrics()

    with pytest.raises(
        TypeError,
        match="duration_seconds must be numeric",
    ):
        metrics.record_trade_success("0.1")  # type: ignore[arg-type]


def test_reset_clears_metrics() -> None:
    metrics = ServiceMetrics()

    metrics.record_trade_success(0.100)
    metrics.record_trade_failure(0.200)
    metrics.record_parse_error()
    metrics.record_ignored_event()
    metrics.record_published_analytics()

    metrics.reset()

    snapshot = metrics.snapshot()

    assert snapshot == ServiceMetricsSnapshot(
        processed_trade_count=0,
        processing_failure_count=0,
        parse_error_count=0,
        ignored_event_count=0,
        published_analytics_count=0,
        total_processing_duration_seconds=0.0,
    )


def test_metrics_are_thread_safe() -> None:
    metrics = ServiceMetrics()

    def record_operations() -> None:
        for _ in range(100):
            metrics.record_trade_success(0.001)
            metrics.record_trade_failure(0.002)
            metrics.record_parse_error()
            metrics.record_ignored_event()
            metrics.record_published_analytics()

    threads = [
        threading.Thread(target=record_operations)
        for _ in range(5)
    ]

    for thread in threads:
        thread.start()

    for thread in threads:
        thread.join()

    snapshot = metrics.snapshot()

    assert snapshot.processed_trade_count == 500
    assert snapshot.processing_failure_count == 500
    assert snapshot.parse_error_count == 500
    assert snapshot.ignored_event_count == 500
    assert snapshot.published_analytics_count == 500
    assert snapshot.trade_attempt_count == 1000
    assert snapshot.total_processing_duration_seconds == pytest.approx(
        1.5,
    )
