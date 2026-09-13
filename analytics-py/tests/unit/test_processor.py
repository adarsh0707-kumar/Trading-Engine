"""Tests for the streaming analytics processor."""

from datetime import datetime, timezone
from decimal import Decimal

from analytics.config.risk_limits import RiskLimitConfig
from analytics.models import (
    AnalyticsResult,
    ProcessedTrade,
    RiskEventType,
    RiskLimitStatus,
    RiskLimitType,
    Trade,
)
from analytics.pipeline.processor import StreamingProcessor


def _trade(
    *,
    event_id: str = "trade-001",
    trade_id: str = "trade-id-001",
    symbol: str = "AAPL",
    price: Decimal = Decimal("100"),
    quantity: int = 1,
    side: str = "BUY",
) -> Trade:
    """Build a deterministic trade for processor tests."""

    return Trade(
        event_id=event_id,
        event_type="TRADE",
        trade_id=trade_id,
        symbol=symbol,
        price=price,
        quantity=quantity,
        taker_side=side,
        timestamp=datetime(
            2026,
            9,
            12,
            10,
            0,
            0,
            tzinfo=timezone.utc,
        ),
    )


def test_process_trade_emits_analytics_update() -> None:
    """The processor should emit a valid analytics update."""

    processor = StreamingProcessor()

    result = processor.process_trade(_trade())

    assert isinstance(result, AnalyticsResult)
    assert result.event_type == "ANALYTICS_UPDATE"
    assert result.symbol == "AAPL"
    assert result.price == Decimal("100")


def test_process_trade_with_risk_events_returns_processed_trade() -> None:
    """The risk-aware API should return analytics and risk events."""

    processor = StreamingProcessor(
        risk_limits=RiskLimitConfig(max_position=10),
    )

    result = processor.process_trade_with_risk_events(
        _trade(quantity=8),
    )

    assert isinstance(result, ProcessedTrade)
    assert isinstance(result.analytics, AnalyticsResult)
    assert result.analytics.event_type == "ANALYTICS_UPDATE"
    assert len(result.risk_events) == 1


def test_process_trade_without_risk_config_returns_no_risk_events() -> None:
    """Risk events should be disabled when no risk configuration is supplied."""

    processor = StreamingProcessor()

    result = processor.process_trade_with_risk_events(_trade())

    assert isinstance(result, ProcessedTrade)
    assert result.risk_events == ()


def test_position_warning_generates_risk_event() -> None:
    """A position reaching the warning threshold should emit a warning."""

    processor = StreamingProcessor(
        risk_limits=RiskLimitConfig(
            max_position=10,
        ),
    )

    result = processor.process_trade_with_risk_events(
        _trade(quantity=8),
    )

    assert len(result.risk_events) == 1

    event = result.risk_events[0]

    assert event.event_type == RiskEventType.LIMIT_WARNING
    assert event.status == RiskLimitStatus.WARNING
    assert event.limit_type == RiskLimitType.MAX_POSITION
    assert event.threshold == Decimal("10")
    assert event.warning_threshold == Decimal("8.0")
    assert event.current_value == Decimal("8")
    assert event.symbol == "AAPL"
    assert event.timestamp == result.analytics.timestamp


def test_position_breach_generates_risk_event() -> None:
    """A position reaching the hard limit should emit a breach event."""

    processor = StreamingProcessor(
        risk_limits=RiskLimitConfig(
            max_position=10,
        ),
    )

    result = processor.process_trade_with_risk_events(
        _trade(quantity=10),
    )

    assert len(result.risk_events) == 1

    event = result.risk_events[0]

    assert event.event_type == RiskEventType.LIMIT_BREACHED
    assert event.status == RiskLimitStatus.BREACHED
    assert event.limit_type == RiskLimitType.MAX_POSITION
    assert event.threshold == Decimal("10")
    assert event.current_value == Decimal("10")
    assert event.symbol == "AAPL"


def test_position_value_breach_generates_risk_event() -> None:
    """Position-value limits should be evaluated using the trade price."""

    processor = StreamingProcessor(
        risk_limits=RiskLimitConfig(
            max_position_value=Decimal("1000"),
        ),
    )

    result = processor.process_trade_with_risk_events(
        _trade(
            price=Decimal("125"),
            quantity=8,
        ),
    )

    assert len(result.risk_events) == 1

    event = result.risk_events[0]

    assert event.event_type == RiskEventType.LIMIT_BREACHED
    assert event.status == RiskLimitStatus.BREACHED
    assert event.limit_type == RiskLimitType.MAX_POSITION_VALUE
    assert event.threshold == Decimal("1000")
    assert event.current_value == Decimal("1000")
    assert event.symbol == "AAPL"


def test_risk_events_are_isolated_between_symbols() -> None:
    """Each symbol should maintain independent risk-event state."""

    processor = StreamingProcessor(
        risk_limits=RiskLimitConfig(
            max_position=1,
        ),
    )

    first = processor.process_trade_with_risk_events(
        _trade(
            event_id="trade-aapl",
            trade_id="trade-id-aapl",
            symbol="AAPL",
            quantity=1,
        ),
    )

    second = processor.process_trade_with_risk_events(
        _trade(
            event_id="trade-msft",
            trade_id="trade-id-msft",
            symbol="MSFT",
            quantity=1,
        ),
    )

    assert len(first.risk_events) == 1
    assert len(second.risk_events) == 1

    first_event = first.risk_events[0]
    second_event = second.risk_events[0]

    assert first_event.symbol == "AAPL"
    assert second_event.symbol == "MSFT"
    assert first_event.event_id != second_event.event_id
    assert "AAPL" in first_event.event_id
    assert "MSFT" in second_event.event_id


def test_process_trade_preserves_backwards_compatible_api() -> None:
    """The original process_trade API should still return AnalyticsResult."""

    processor = StreamingProcessor(
        risk_limits=RiskLimitConfig(
            max_position=10,
        ),
    )

    result = processor.process_trade(
        _trade(quantity=8),
    )

    assert isinstance(result, AnalyticsResult)
    assert not isinstance(result, ProcessedTrade)
    assert result.event_type == "ANALYTICS_UPDATE"


def test_event_ids_are_unique_for_multiple_risk_events() -> None:
    """Multiple generated risk events should receive unique IDs."""

    processor = StreamingProcessor(
        risk_limits=RiskLimitConfig(
            max_position=10,
            max_position_value=Decimal("1000"),
        ),
    )

    result = processor.process_trade_with_risk_events(
        _trade(
            quantity=10,
            price=Decimal("100"),
        ),
    )

    event_ids = [event.event_id for event in result.risk_events]

    assert len(event_ids) == 2
    assert len(set(event_ids)) == 2
