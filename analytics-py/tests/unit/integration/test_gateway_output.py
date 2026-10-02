import json
from datetime import datetime, timezone
from decimal import Decimal

from analytics.integration.gateway_message import (
    serialize_analytics_update,
    serialize_risk_event,
)
from analytics.models.analytics_result import AnalyticsResult
from analytics.models.risk_event import RiskEvent
from analytics.models.risk_limit import (
    RiskLimitStatus,
    RiskLimitType,
)


def analytics_result() -> AnalyticsResult:
    return AnalyticsResult(
        event_id="analytics-trade-1-1",
        event_type="ANALYTICS_UPDATE",
        symbol="SIM",
        price=Decimal("100.25"),
        vwap=Decimal("100.25"),
        sma=Decimal("100.25"),
        ema=Decimal("100.25"),
        position=10,
        realized_pnl=Decimal("0"),
        unrealized_pnl=Decimal("0"),
        equity=Decimal("10000"),
        peak_equity=Decimal("10000"),
        drawdown=Decimal("0"),
        timestamp=datetime(2026, 10, 2, 12, 0, 1, tzinfo=timezone.utc),
    )


def risk_event() -> RiskEvent:
    return RiskEvent(
        event_id="risk-SIM-1",
        event_type="RISK_LIMIT_BREACHED",
        symbol="SIM",
        limit_type=RiskLimitType.MAX_DRAWDOWN,
        status=RiskLimitStatus.BREACHED,
        threshold=Decimal("100"),
        warning_threshold=Decimal("80"),
        current_value=Decimal("120"),
        timestamp=datetime(2026, 10, 2, 12, 0, 1, tzinfo=timezone.utc),
    )


def test_serializes_analytics_update_envelope() -> None:
    message = json.loads(serialize_analytics_update(analytics_result()))

    assert message["version"] == 1
    assert message["type"] == "ANALYTICS_UPDATE"
    assert message["event_id"] == "analytics-trade-1-1"
    assert message["request_id"] == "analytics-trade-1-1"

    payload = json.loads(message["payload"])
    assert payload["equity"] == "10000"
    assert payload["drawdown"] == "0"


def test_serializes_risk_event_envelope() -> None:
    message = json.loads(serialize_risk_event(risk_event()))

    assert message["version"] == 1
    assert message["type"] == "RISK_EVENT"
    assert message["event_id"] == "risk-SIM-1"
    assert message["request_id"] == "risk-SIM-1"

    payload = json.loads(message["payload"])
    assert payload["status"] == "breached"
    assert payload["limit_type"] == "MAX_DRAWDOWN"
