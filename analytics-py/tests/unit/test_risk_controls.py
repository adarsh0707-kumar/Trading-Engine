"""Regression tests for runtime analytics risk controls."""

from datetime import datetime, timedelta, timezone
from decimal import Decimal

from analytics.config.settings import Settings
from analytics.models import RiskEventType, RiskLimitType, Trade
from analytics.pipeline.processor import StreamingProcessor


def _trade(*, event_id: str, price: str, side: str, timestamp: datetime) -> Trade:
    return Trade(
        event_id=event_id,
        event_type="TRADE",
        trade_id=event_id,
        symbol="AAPL",
        price=Decimal(price),
        quantity=1,
        timestamp=timestamp,
        taker_side=side,
    )


def test_runtime_settings_enable_validated_risk_limits(monkeypatch) -> None:
    monkeypatch.setenv("TRADING_ENGINE_RISK_MAX_POSITION", "20")
    monkeypatch.setenv("TRADING_ENGINE_RISK_MAX_POSITION_VALUE", "2500")
    monkeypatch.setenv("TRADING_ENGINE_RISK_MAX_DRAWDOWN", "400")
    monkeypatch.setenv("TRADING_ENGINE_RISK_MAX_DAILY_LOSS", "125")
    monkeypatch.setenv("TRADING_ENGINE_RISK_WARNING_RATIO", "0.75")

    settings = Settings.from_environment()

    assert settings.risk_limit_config.max_position == 20
    assert settings.risk_limit_config.max_position_value == Decimal("2500")
    assert settings.risk_limit_config.max_drawdown == Decimal("400")
    assert settings.risk_limit_config.max_daily_loss == Decimal("125")
    assert settings.risk_limit_config.warning_ratio == Decimal("0.75")


def test_invalid_risk_limit_configuration_is_rejected(monkeypatch) -> None:
    monkeypatch.setenv("TRADING_ENGINE_RISK_MAX_DAILY_LOSS", "0")

    try:
        Settings.from_environment()
    except ValueError as exc:
        assert "max_daily_loss" in str(exc)
    else:
        raise AssertionError("invalid risk threshold should be rejected")


def test_daily_loss_uses_intraday_equity_change() -> None:
    settings = Settings(
        risk_max_position=100,
        risk_max_position_value=Decimal("100000"),
        risk_max_drawdown=Decimal("100000"),
        risk_max_daily_loss=Decimal("10"),
    )
    processor = StreamingProcessor(risk_limits=settings.risk_limit_config)
    start = datetime(2026, 10, 9, 10, 0, tzinfo=timezone.utc)

    processor.process_trade_with_risk_events(
        _trade(event_id="open-long", price="100", side="BUY", timestamp=start)
    )
    result = processor.process_trade_with_risk_events(
        _trade(
            event_id="close-long-at-loss",
            price="90",
            side="SELL",
            timestamp=start + timedelta(minutes=1),
        )
    )

    daily_loss_events = [
        event for event in result.risk_events
        if event.limit_type == RiskLimitType.MAX_DAILY_LOSS
    ]
    assert len(daily_loss_events) == 1
    assert daily_loss_events[0].event_type == RiskEventType.LIMIT_BREACHED
    assert daily_loss_events[0].current_value == Decimal("10")


def test_daily_loss_baseline_resets_on_new_trade_day() -> None:
    settings = Settings(
        risk_max_position=100,
        risk_max_position_value=Decimal("100000"),
        risk_max_drawdown=Decimal("100000"),
        risk_max_daily_loss=Decimal("10"),
    )
    processor = StreamingProcessor(risk_limits=settings.risk_limit_config)
    start = datetime(2026, 10, 9, 10, 0, tzinfo=timezone.utc)

    processor.process_trade_with_risk_events(
        _trade(event_id="open-long", price="100", side="BUY", timestamp=start)
    )
    processor.process_trade_with_risk_events(
        _trade(
            event_id="close-long-at-loss",
            price="90",
            side="SELL",
            timestamp=start + timedelta(minutes=1),
        )
    )
    next_day = processor.process_trade_with_risk_events(
        _trade(
            event_id="next-day-flat",
            price="90",
            side="BUY",
            timestamp=start + timedelta(days=1),
        )
    )

    daily_loss_events = [
        event for event in next_day.risk_events
        if event.limit_type == RiskLimitType.MAX_DAILY_LOSS
    ]
    assert daily_loss_events == []
