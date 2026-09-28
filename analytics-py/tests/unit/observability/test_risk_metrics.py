"""Tests for portfolio risk metrics."""

from decimal import Decimal
import threading

import pytest

from analytics.observability import RiskMetrics, RiskMetricsSnapshot


def snapshot(**overrides):
    values = {
        "position": 10,
        "realized_pnl": Decimal("12.50"),
        "unrealized_pnl": Decimal("-2.50"),
        "equity": Decimal("1010"),
        "peak_equity": Decimal("1020"),
        "drawdown": Decimal("10"),
    }
    values.update(overrides)
    return values


def test_new_risk_metrics_are_empty() -> None:
    metrics = RiskMetrics()

    result = metrics.snapshot()

    assert result == RiskMetricsSnapshot(
        sample_count=0,
        current_position=0,
        max_abs_position=0,
        current_realized_pnl=Decimal("0"),
        current_unrealized_pnl=Decimal("0"),
        current_equity=Decimal("0"),
        peak_equity=Decimal("0"),
        current_drawdown=Decimal("0"),
        max_drawdown=Decimal("0"),
        warning_event_count=0,
        breached_event_count=0,
    )


def test_record_snapshot_updates_current_and_peak_metrics() -> None:
    metrics = RiskMetrics()

    metrics.record_snapshot(**snapshot(position=10, drawdown=Decimal("5")))
    metrics.record_snapshot(**snapshot(
        position=-25,
        realized_pnl=Decimal("20"),
        drawdown=Decimal("18"),
    ))

    result = metrics.snapshot()

    assert result.sample_count == 2
    assert result.current_position == -25
    assert result.max_abs_position == 25
    assert result.current_realized_pnl == Decimal("20")
    assert result.current_drawdown == Decimal("18")
    assert result.max_drawdown == Decimal("18")


def test_risk_event_counts_accumulate() -> None:
    metrics = RiskMetrics()

    metrics.record_warning_event()
    metrics.record_warning_event()
    metrics.record_breached_event()

    result = metrics.snapshot()

    assert result.warning_event_count == 2
    assert result.breached_event_count == 1


def test_drawdown_cannot_be_negative() -> None:
    metrics = RiskMetrics()

    with pytest.raises(
        ValueError,
        match="drawdown must not be negative",
    ):
        metrics.record_snapshot(**snapshot(drawdown=Decimal("-1")))


def test_risk_values_must_use_decimal() -> None:
    metrics = RiskMetrics()

    with pytest.raises(TypeError, match="risk values must be Decimal"):
        metrics.record_snapshot(**snapshot(equity=1010))


def test_position_must_be_integer() -> None:
    metrics = RiskMetrics()

    with pytest.raises(TypeError, match="position must be an integer"):
        metrics.record_snapshot(**snapshot(position=1.5))


def test_reset_clears_all_risk_metrics() -> None:
    metrics = RiskMetrics()

    metrics.record_snapshot(**snapshot())
    metrics.record_warning_event()
    metrics.record_breached_event()
    metrics.reset()

    assert metrics.snapshot().sample_count == 0
    assert metrics.snapshot().max_abs_position == 0
    assert metrics.snapshot().max_drawdown == Decimal("0")
    assert metrics.snapshot().warning_event_count == 0
    assert metrics.snapshot().breached_event_count == 0


def test_snapshot_is_immutable() -> None:
    metrics = RiskMetrics()
    metrics.record_snapshot(**snapshot())

    result = metrics.snapshot()

    with pytest.raises(AttributeError):
        result.current_equity = Decimal("999")  # type: ignore[misc]


def test_risk_metrics_are_thread_safe() -> None:
    metrics = RiskMetrics()

    def record() -> None:
        for _ in range(100):
            metrics.record_snapshot(**snapshot(position=7, drawdown=Decimal("3")))

    threads = [threading.Thread(target=record) for _ in range(5)]
    for thread in threads:
        thread.start()
    for thread in threads:
        thread.join()

    result = metrics.snapshot()

    assert result.sample_count == 500
    assert result.current_position == 7
    assert result.max_abs_position == 7
