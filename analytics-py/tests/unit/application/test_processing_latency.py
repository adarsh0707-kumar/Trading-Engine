"""Application tests for processing latency instrumentation."""

from datetime import datetime, timezone
from decimal import Decimal
from unittest.mock import Mock

import pytest

from analytics.config.settings import Settings
from analytics.main import AnalyticsService
from analytics.models import AnalyticsResult, Trade
from analytics.observability import ProcessingLatencyMetrics


def _trade() -> Trade:
    """Build a deterministic trade for latency instrumentation tests."""
    return Trade(
        event_id="latency-trade-001",
        event_type="TRADE",
        trade_id="latency-trade-id-001",
        symbol="AAPL",
        price=Decimal("100"),
        quantity=8,
        taker_side="BUY",
        timestamp=datetime(
            2026,
            9,
            27,
            10,
            0,
            0,
            tzinfo=timezone.utc,
        ),
    )


def test_service_accepts_injected_processing_latency_metrics() -> None:
    metrics = ProcessingLatencyMetrics()

    service = AnalyticsService(
        Settings(),
        publish_sink=Mock(),
        processing_latency_metrics=metrics,
    )

    assert service.processing_latency_metrics is metrics


def test_successful_trade_records_processing_latency() -> None:
    metrics = ProcessingLatencyMetrics()
    service = AnalyticsService(
        Settings(),
        publish_sink=Mock(),
        processing_latency_metrics=metrics,
    )

    service.parser.parse = Mock(return_value=_trade())
    trade = _trade()
    result = Mock()
    result.analytics = AnalyticsResult(
        event_id=trade.event_id,
        event_type="ANALYTICS_UPDATE",
        symbol=trade.symbol,
        price=trade.price,
        vwap=Decimal("100"),
        sma=None,
        ema=None,
        position=8,
        realized_pnl=Decimal("0"),
        unrealized_pnl=Decimal("0"),
        equity=Decimal("10000"),
        peak_equity=Decimal("10000"),
        drawdown=Decimal("0"),
        timestamp=trade.timestamp,
    )
    service.processor.process_trade_with_risk_events = Mock(
        return_value=result,
    )

    service._handle_message("ignored by mocked parser")

    snapshot = metrics.snapshot()

    assert snapshot.sample_count == 1
    assert snapshot.total_duration_seconds > 0.0
    assert snapshot.average_duration_seconds > 0.0


def test_failed_trade_records_processing_latency() -> None:
    metrics = ProcessingLatencyMetrics()
    service = AnalyticsService(
        Settings(),
        publish_sink=Mock(),
        processing_latency_metrics=metrics,
    )

    service.parser.parse = Mock(return_value=_trade())
    service.processor.process_trade_with_risk_events = Mock(
        side_effect=ValueError("invalid trade"),
    )

    service._handle_message("ignored by mocked parser")

    snapshot = metrics.snapshot()

    assert snapshot.sample_count == 1
    assert snapshot.total_duration_seconds > 0.0


def test_processing_latency_is_recorded_for_trade_pipeline_only() -> None:
    metrics = ProcessingLatencyMetrics()
    service = AnalyticsService(
        Settings(),
        publish_sink=Mock(),
        processing_latency_metrics=metrics,
    )

    service.parser.parse = Mock(return_value=Mock(event_type="MARKET_TICK"))

    service._handle_message("ignored by mocked parser")

    assert metrics.snapshot().sample_count == 0
