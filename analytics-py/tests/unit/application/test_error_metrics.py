"""Application tests for error-counter instrumentation."""

from datetime import datetime, timezone
from decimal import Decimal
from unittest.mock import MagicMock, Mock

from analytics.models import Trade

from analytics.config.settings import Settings
from analytics.main import AnalyticsService
from analytics.observability import ErrorMetrics
import pytest


def test_service_accepts_injected_error_metrics() -> None:
    metrics = ErrorMetrics()
    service = AnalyticsService(
        Settings(),
        publish_sink=Mock(),
        error_metrics=metrics,
    )
    assert service.error_metrics is metrics


def test_parse_failure_updates_error_counter() -> None:
    metrics = ErrorMetrics()
    service = AnalyticsService(Settings(), publish_sink=Mock(), error_metrics=metrics)

    service._handle_message("{invalid-json")

    assert metrics.snapshot().parse_error_count == 1


def test_processing_failure_updates_error_counter() -> None:
    metrics = ErrorMetrics()
    service = AnalyticsService(Settings(), publish_sink=Mock(), error_metrics=metrics)
    service.parser.parse = Mock(return_value=Trade(
        event_id="processing-001",
        event_type="TRADE",
        trade_id="processing-trade-001",
        symbol="AAPL",
        price=Decimal("100"),
        quantity=8,
        taker_side="BUY",
        timestamp=datetime.now(timezone.utc),
    ))
    service.processor.process_trade_with_risk_events = Mock(
        side_effect=ValueError("processing failure"),
    )

    service._handle_message("valid-enough-for-test")

    assert metrics.snapshot().processing_error_count == 1


def test_persistence_failure_updates_error_counter() -> None:
    metrics = ErrorMetrics()
    repositories = Mock()
    transaction = MagicMock()
    transaction.__enter__.return_value = transaction
    transaction.__exit__.return_value = False
    repositories.connection.transaction.return_value = transaction
    repositories.analytics.save.side_effect = RuntimeError("database unavailable")

    service = AnalyticsService(
        Settings(),
        repositories=repositories,
        publish_sink=Mock(),
        error_metrics=metrics,
    )

    message = (
        '{"type":"TRADE","request_id":"error-counter-persistence",'
        '"timestamp":"2026-09-27T10:00:00+00:00",'
        '"payload":"{\"symbol\":\"AAPL\",\"price\":\"100\",'
        '\"quantity\":8,\"taker_order_id\":\"order-taker\",'
        '\"maker_order_id\":\"order-maker\",\"taker_side\":\"BUY\"}"}'
    )
    service._handle_message(message)

    assert metrics.snapshot().persistence_error_count == 1


def test_publish_failure_updates_error_counter_and_does_not_publish_count() -> None:
    metrics = ErrorMetrics()
    sink = Mock(side_effect=RuntimeError("publisher unavailable"))
    service = AnalyticsService(
        Settings(),
        publish_sink=sink,
        error_metrics=metrics,
    )

    message = (
        '{"type":"TRADE","request_id":"error-counter-publish",'
        '"timestamp":"2026-09-27T10:00:00+00:00",'
        '"payload":"{\"symbol\":\"AAPL\",\"price\":\"100\",'
        '\"quantity\":8,\"taker_order_id\":\"order-taker\",'
        '\"maker_order_id\":\"order-maker\",\"taker_side\":\"BUY\"}"}'
    )
    service._handle_message(message)

    snapshot = metrics.snapshot()
    assert snapshot.publish_error_count == 1
