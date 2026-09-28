"""Application tests for trade throughput instrumentation."""

from datetime import datetime, timezone
from decimal import Decimal

from unittest.mock import Mock

from analytics.models import AnalyticsResult, Trade

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

    trade = Trade(
        event_id="throughput-trade-001",
        event_type="TRADE",
        trade_id="throughput-trade-001",
        symbol="AAPL",
        quantity=10,
        price=Decimal("100"),
        timestamp=datetime.now(timezone.utc),
        taker_side="BUY",
    )
    result = Mock()
    result.analytics = AnalyticsResult(
        event_id=trade.event_id,
        event_type="ANALYTICS_UPDATE",
        symbol=trade.symbol,
        price=trade.price,
        vwap=None,
        sma=None,
        ema=None,
        position=10,
        realized_pnl=Decimal("0"),
        unrealized_pnl=Decimal("0"),
        equity=Decimal("0"),
        peak_equity=Decimal("0"),
        drawdown=Decimal("0"),
        timestamp=trade.timestamp,
    )

    service.parser.parse = Mock(return_value=trade)
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

    service.parser.parse = Mock(return_value=Trade(
        event_id="throughput-failure-001",
        event_type="TRADE",
        trade_id="throughput-failure-001",
        symbol="AAPL",
        quantity=10,
        price=Decimal("100"),
        timestamp=datetime.now(timezone.utc),
        taker_side="BUY",
    ))
    service.processor.process_trade_with_risk_events = Mock(
        side_effect=ValueError("invalid trade"),
    )

    service._handle_message("ignored by mocked parser")

    assert metrics.snapshot().total_trade_count == 0
