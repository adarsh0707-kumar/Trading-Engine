"""Application tests for trade throughput instrumentation."""

from unittest.mock import Mock

from analytics.config.settings import Settings
from analytics.main import AnalyticsService
from analytics.observability import TradeThroughputMetrics


def test_service_accepts_injected_trade_throughput_metrics() -> None:
    metrics = TradeThroughputMetrics()

    service = AnalyticsService(
        Settings(),
        publish_sink=Mock(),
        trade_throughput_metrics=metrics,
    )

    assert service.trade_throughput_metrics is metrics


def test_successful_trade_updates_throughput_metrics() -> None:
    metrics = TradeThroughputMetrics()
    service = AnalyticsService(
        Settings(),
        publish_sink=Mock(),
        trade_throughput_metrics=metrics,
    )

    result = Mock()
    result.analytics = object()

    service.parser.parse = Mock(return_value=Mock(
        event_type="TRADE",
        event_id="throughput-trade-001",
    ))
    service.processor.process_trade_with_risk_events = Mock(
        return_value=result,
    )

    service._handle_message("ignored by mocked parser")

    snapshot = metrics.snapshot()

    assert snapshot.trade_count == 1
    assert snapshot.total_trade_count == 1
    assert snapshot.trades_per_second > 0.0


def test_failed_trade_does_not_count_as_processed_throughput() -> None:
    metrics = TradeThroughputMetrics()
    service = AnalyticsService(
        Settings(),
        publish_sink=Mock(),
        trade_throughput_metrics=metrics,
    )

    service.parser.parse = Mock(return_value=Mock(
        event_type="TRADE",
        event_id="throughput-failure-001",
    ))
    service.processor.process_trade_with_risk_events = Mock(
        side_effect=ValueError("invalid trade"),
    )

    service._handle_message("ignored by mocked parser")

    assert metrics.snapshot().total_trade_count == 0
