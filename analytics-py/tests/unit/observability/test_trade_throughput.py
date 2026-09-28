"""Tests for trade throughput metrics."""

from __future__ import annotations

import threading

import pytest

from analytics.observability import (
    TradeThroughputMetrics,
    TradeThroughputSnapshot,
)


def test_new_throughput_metrics_are_empty() -> None:
    metrics = TradeThroughputMetrics(window_seconds=10.0)

    snapshot = metrics.snapshot(timestamp_seconds=100.0)

    assert snapshot == TradeThroughputSnapshot(
        trade_count=0,
        window_seconds=10.0,
        trades_per_second=0.0,
        total_trade_count=0,
    )


def test_snapshot_reports_recent_trade_throughput() -> None:
    metrics = TradeThroughputMetrics(window_seconds=10.0)

    metrics.record_trade(timestamp_seconds=100.0)
    metrics.record_trade(timestamp_seconds=103.0)
    metrics.record_trade(timestamp_seconds=109.0)

    snapshot = metrics.snapshot(timestamp_seconds=109.0)

    assert snapshot.trade_count == 3
    assert snapshot.window_seconds == 10.0
    assert snapshot.trades_per_second == pytest.approx(0.3)
    assert snapshot.total_trade_count == 3


def test_old_trades_are_excluded_from_window() -> None:
    metrics = TradeThroughputMetrics(window_seconds=10.0)

    metrics.record_trade(timestamp_seconds=80.0)
    metrics.record_trade(timestamp_seconds=90.0)
    metrics.record_trade(timestamp_seconds=99.999)

    snapshot = metrics.snapshot(timestamp_seconds=100.0)

    assert snapshot.trade_count == 2
    assert snapshot.trades_per_second == pytest.approx(0.2)
    assert snapshot.total_trade_count == 3


def test_default_window_is_sixty_seconds() -> None:
    metrics = TradeThroughputMetrics()

    metrics.record_trade(timestamp_seconds=100.0)

    snapshot = metrics.snapshot(timestamp_seconds=100.0)

    assert snapshot.window_seconds == 60.0
    assert snapshot.trade_count == 1


def test_invalid_window_is_rejected() -> None:
    with pytest.raises(
        ValueError,
        match="window_seconds must be positive",
    ):
        TradeThroughputMetrics(window_seconds=0)


def test_non_numeric_window_is_rejected() -> None:
    with pytest.raises(
        TypeError,
        match="window_seconds must be numeric",
    ):
        TradeThroughputMetrics(window_seconds="60")  # type: ignore[arg-type]


def test_reset_clears_throughput_metrics() -> None:
    metrics = TradeThroughputMetrics(window_seconds=10.0)

    metrics.record_trade(timestamp_seconds=100.0)
    metrics.record_trade(timestamp_seconds=101.0)
    metrics.reset()

    snapshot = metrics.snapshot(timestamp_seconds=101.0)

    assert snapshot.trade_count == 0
    assert snapshot.trades_per_second == 0.0
    assert snapshot.total_trade_count == 0


def test_throughput_metrics_are_thread_safe() -> None:
    metrics = TradeThroughputMetrics(window_seconds=1000.0)

    def record_operations() -> None:
        for index in range(100):
            metrics.record_trade(timestamp_seconds=100.0 + index)

    threads = [
        threading.Thread(target=record_operations)
        for _ in range(5)
    ]

    for thread in threads:
        thread.start()

    for thread in threads:
        thread.join()

    snapshot = metrics.snapshot(timestamp_seconds=200.0)

    assert snapshot.trade_count == 500
    assert snapshot.total_trade_count == 500
