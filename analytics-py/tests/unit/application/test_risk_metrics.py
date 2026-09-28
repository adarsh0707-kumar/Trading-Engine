"""Application tests for risk metrics instrumentation."""

from decimal import Decimal
from unittest.mock import Mock

from analytics.config.settings import Settings
from analytics.main import AnalyticsService
from analytics.models import AnalyticsResult, ProcessedTrade, RiskEvent, Trade
from analytics.models.risk_event import RiskEventType
from analytics.models.risk_limit import RiskLimit, RiskLimitStatus, RiskLimitType
from analytics.observability import RiskMetrics
from analytics.risk.risk_manager import RiskSnapshot
from datetime import datetime, timezone


def make_trade() -> Trade:
    return Trade(
        event_id="risk-metrics-001",
        symbol="AAPL",
        quantity=10,
        price=Decimal("100"),
        side="BUY",
        timestamp=datetime.now(timezone.utc),
    )


def make_result() -> ProcessedTrade:
    trade = make_trade()
    snapshot = RiskSnapshot(
        position=10,
        average_entry_price=Decimal("100"),
        realized_pnl=Decimal("5"),
        unrealized_pnl=Decimal("15"),
        equity=Decimal("1020"),
        peak_equity=Decimal("1030"),
        drawdown=Decimal("10"),
    )
    return ProcessedTrade(
        trade=trade,
        analytics=AnalyticsResult(\n            event_id=trade.event_id,\n            event_type="ANALYTICS_UPDATE",\n            symbol=trade.symbol,\n            price=trade.price,\n            vwap=None,\n            sma=None,\n            ema=None,\n            position=snapshot.position,\n            realized_pnl=snapshot.realized_pnl,\n            unrealized_pnl=snapshot.unrealized_pnl,\n            equity=snapshot.equity,\n            peak_equity=snapshot.peak_equity,\n            drawdown=snapshot.drawdown,\n            timestamp=trade.timestamp,\n        ),
        risk_snapshot=snapshot,
        risk_events=(),
    )


def test_service_accepts_injected_risk_metrics() -> None:
    metrics = RiskMetrics()
    service = AnalyticsService(
        Settings(),
        publish_sink=Mock(),
        risk_metrics=metrics,
    )

    assert service.risk_metrics is metrics


def test_successful_trade_records_risk_snapshot() -> None:
    metrics = RiskMetrics()
    service = AnalyticsService(
        Settings(),
        publish_sink=Mock(),
        risk_metrics=metrics,
    )
    result = make_result()
    service.parser.parse = Mock(return_value=result.trade)
    service.processor.process_trade_with_risk_events = Mock(
        return_value=result,
    )

    service._handle_message("ignored by mocked parser")

    snapshot = metrics.snapshot()

    assert snapshot.sample_count == 1
    assert snapshot.current_position == 10
    assert snapshot.current_equity == Decimal("1020")
    assert snapshot.current_drawdown == Decimal("10")


def test_risk_events_update_event_counters() -> None:
    metrics = RiskMetrics()
    service = AnalyticsService(
        Settings(),
        publish_sink=Mock(),
        risk_metrics=metrics,
    )
    result = make_result()
    warning = RiskEvent(
        event_id="warning-001",
        event_type=RiskEventType.LIMIT_WARNING,
        symbol="AAPL",
        limit_type=RiskLimitType.MAX_POSITION,
        status=RiskLimitStatus.WARNING,
        threshold=Decimal("100"),
        warning_threshold=Decimal("80"),
        current_value=Decimal("85"),
        timestamp=datetime.now(timezone.utc),
    )
    breached = RiskEvent(
        event_id="breach-001",
        event_type=RiskEventType.LIMIT_BREACHED,
        symbol="AAPL",
        limit_type=RiskLimitType.MAX_POSITION,
        status=RiskLimitStatus.BREACHED,
        threshold=Decimal("100"),
        warning_threshold=Decimal("80"),
        current_value=Decimal("110"),
        timestamp=datetime.now(timezone.utc),
    )
    result = ProcessedTrade(
        trade=result.trade,
        analytics=result.analytics,
        risk_snapshot=result.risk_snapshot,
        risk_events=(warning, breached),
    )
    service.parser.parse = Mock(return_value=result.trade)
    service.processor.process_trade_with_risk_events = Mock(return_value=result)

    service._handle_message("ignored by mocked parser")

    snapshot = metrics.snapshot()
    assert snapshot.warning_event_count == 1
    assert snapshot.breached_event_count == 1
