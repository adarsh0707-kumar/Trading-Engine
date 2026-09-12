"""Unit tests for the analytics result publisher."""

from datetime import datetime, timezone
from decimal import Decimal
import json

import pytest

from analytics.models import AnalyticsResult
from analytics.pipeline import AnalyticsPublisher


def make_result() -> AnalyticsResult:
    """Create a valid AnalyticsResult for publisher tests."""

    return AnalyticsResult(
        event_id="analytics-SIM-000001",
        event_type="ANALYTICS_UPDATE",
        symbol="SIM",
        price=Decimal("101.25"),
        vwap=Decimal("100.75"),
        sma=Decimal("100.50"),
        ema=Decimal("100.90"),
        position=10,
        realized_pnl=Decimal("25.00"),
        unrealized_pnl=Decimal("12.50"),
        equity=Decimal("10037.50"),
        peak_equity=Decimal("10050.00"),
        drawdown=Decimal("12.50"),
        timestamp=datetime(2026, 9, 12, 18, 30, 0, tzinfo=timezone.utc),
    )


def test_publish_serializes_analytics_result() -> None:
    """Publisher should serialize an AnalyticsResult as JSON."""

    published: list[str] = []
    publisher = AnalyticsPublisher(published.append)

    result = make_result()

    publisher.publish(result)

    assert len(published) == 1

    payload = json.loads(published[0])

    assert payload["event_id"] == "analytics-SIM-000001"
    assert payload["event_type"] == "ANALYTICS_UPDATE"
    assert payload["symbol"] == "SIM"
    assert payload["price"] == "101.25"
    assert payload["vwap"] == "100.75"
    assert payload["sma"] == "100.50"
    assert payload["ema"] == "100.90"
    assert payload["position"] == 10
    assert payload["realized_pnl"] == "25.00"
    assert payload["unrealized_pnl"] == "12.50"
    assert payload["equity"] == "10037.50"
    assert payload["peak_equity"] == "10050.00"
    assert payload["drawdown"] == "12.50"
    assert payload["timestamp"] == "2026-09-12T18:30:00+00:00"


def test_publish_preserves_nullable_indicator_values() -> None:
    """Publisher should preserve None indicator values as JSON null."""

    published: list[str] = []
    publisher = AnalyticsPublisher(published.append)

    result = AnalyticsResult(
        event_id="analytics-SIM-000002",
        event_type="ANALYTICS_UPDATE",
        symbol="SIM",
        price=Decimal("99.50"),
        vwap=None,
        sma=None,
        ema=None,
        position=0,
        realized_pnl=Decimal("0"),
        unrealized_pnl=Decimal("0"),
        equity=Decimal("10000"),
        peak_equity=Decimal("10000"),
        drawdown=Decimal("0"),
        timestamp=datetime(2026, 9, 12, 18, 31, 0, tzinfo=timezone.utc),
    )

    publisher.publish(result)

    payload = json.loads(published[0])

    assert payload["vwap"] is None
    assert payload["sma"] is None
    assert payload["ema"] is None


def test_publish_calls_sink_once_per_result() -> None:
    """Each publish call should invoke the sink exactly once."""

    published: list[str] = []
    publisher = AnalyticsPublisher(published.append)

    result = make_result()

    publisher.publish(result)
    publisher.publish(result)

    assert len(published) == 2


def test_publisher_requires_callable_sink() -> None:
    """Publisher should reject a non-callable sink."""

    with pytest.raises(TypeError, match="sink must be callable"):
        AnalyticsPublisher("not-callable")  # type: ignore[arg-type]


def test_publish_requires_analytics_result() -> None:
    """Publisher should reject objects of the wrong type."""

    published: list[str] = []
    publisher = AnalyticsPublisher(published.append)

    with pytest.raises(TypeError, match="result must be an AnalyticsResult"):
        publisher.publish({"event_type": "ANALYTICS_UPDATE"})  # type: ignore[arg-type]


def test_published_payload_is_compact_json() -> None:
    """Publisher should produce compact, valid JSON."""

    published: list[str] = []
    publisher = AnalyticsPublisher(published.append)

    publisher.publish(make_result())

    payload = published[0]

    assert "\n" not in payload
    assert ": " not in payload
    assert json.loads(payload)["event_type"] == "ANALYTICS_UPDATE"
