"""Tests for the analytics application service."""

from datetime import datetime, timezone
from decimal import Decimal
from unittest.mock import Mock

from analytics.config.settings import Settings
from analytics.main import AnalyticsService
from analytics.models import (
    AnalyticsResult,
    ProcessedTrade,
    RiskEvent,
    Trade,
)
from analytics.risk.risk_manager import RiskSnapshot


def _trade(
    *,
    event_id: str = "trade-001",
    trade_id: str = "trade-id-001",
    symbol: str = "AAPL",
    price: Decimal = Decimal("100"),
    quantity: int = 8,
) -> Trade:
    """Build a deterministic trade for service tests."""

    return Trade(
        event_id=event_id,
        event_type="TRADE",
        trade_id=trade_id,
        symbol=symbol,
        price=price,
        quantity=quantity,
        taker_side="BUY",
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


def _processed_trade() -> ProcessedTrade:
    """Build a deterministic processed trade for persistence tests."""

    trade = _trade()

    snapshot = RiskSnapshot(
        position=8,
        average_entry_price=Decimal("100"),
        realized_pnl=Decimal("0"),
        unrealized_pnl=Decimal("0"),
        equity=Decimal("10000"),
        peak_equity=Decimal("10000"),
        drawdown=Decimal("0"),
    )

    analytics = AnalyticsResult(
        event_id="analytics-trade-001-1",
        event_type="ANALYTICS_UPDATE",
        symbol="AAPL",
        price=Decimal("100"),
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

    return ProcessedTrade(
        trade=trade,
        analytics=analytics,
        risk_snapshot=snapshot,
        risk_events=(),
    )


def _service(
    *,
    repositories=None,
    settings: Settings | None = None,
) -> AnalyticsService:
    """Build a service with a mocked socket client."""

    service = AnalyticsService(
        settings or Settings(),
        repositories=repositories,
        publish_sink=Mock(),
    )

    service.client = Mock()

    return service


def test_database_disabled_does_not_create_repositories(
    monkeypatch,
) -> None:
    """The service should not create PostgreSQL without a database URL."""

    factory = Mock()

    monkeypatch.setattr(
        "analytics.main.create_postgres_repositories",
        factory,
    )

    service = _service(settings=Settings(database_url=None))

    assert service.repositories is None
    assert service._owns_repositories is False
    factory.assert_not_called()


def test_database_url_creates_owned_repositories(monkeypatch) -> None:
    """A configured database URL should create service-owned repositories."""

    repositories = Mock()

    factory = Mock(return_value=repositories)

    monkeypatch.setattr(
        "analytics.main.create_postgres_repositories",
        factory,
    )

    settings = Settings(
        database_url="postgresql://trading-engine",
    )

    service = _service(settings=settings)

    assert service.repositories is repositories
    assert service._owns_repositories is True
    factory.assert_called_once_with(
        "postgresql://trading-engine",
    )


def test_injected_repositories_are_not_owned() -> None:
    """Injected repositories should remain owned by their caller."""

    repositories = Mock()

    service = _service(repositories=repositories)

    assert service.repositories is repositories
    assert service._owns_repositories is False


def test_persist_saves_complete_processed_trade() -> None:
    """Persistence should receive every required processed-trade value."""

    repositories = Mock()
    result = _processed_trade()

    service = _service(repositories=repositories)

    service._persist(result)

    repositories.trades.save.assert_called_once_with(result.trade)
    repositories.analytics.save.assert_called_once_with(result.analytics)

    repositories.positions.save.assert_called_once_with(
        symbol="AAPL",
        snapshot=result.risk_snapshot,
    )

    repositories.risk.save_risk_state.assert_called_once_with(
        symbol="AAPL",
        snapshot=result.risk_snapshot,
    )

    repositories.risk.save_event.assert_not_called()


def test_persist_saves_all_risk_events() -> None:
    """Every generated risk event should be persisted."""

    repositories = Mock()
    result = _processed_trade()

    event_one = Mock(spec=RiskEvent)
    event_two = Mock(spec=RiskEvent)

    result = ProcessedTrade(
        trade=result.trade,
        analytics=result.analytics,
        risk_snapshot=result.risk_snapshot,
        risk_events=(event_one, event_two),
    )

    service = _service(repositories=repositories)

    service._persist(result)

    assert repositories.risk.save_event.call_count == 2
    repositories.risk.save_event.assert_any_call(event=event_one)
    repositories.risk.save_event.assert_any_call(event=event_two)


def test_handle_message_persists_and_publishes_trade() -> None:
    """A valid trade should be persisted before its analytics are published."""

    repositories = Mock()
    publish_sink = Mock()

    service = AnalyticsService(
        Settings(),
        repositories=repositories,
        publish_sink=publish_sink,
    )

    service._handle_message(
        '{"type":"TRADE",'
        '"request_id":"event-001",'
        '"timestamp":"2026-09-12T10:00:00+00:00",'
        '"payload":"{'
        '\\"symbol\\":\\"AAPL\\",'
        '\\"price\\":\\"100\\",'
        '\\"quantity\\":8,'
        '\\"taker_order_id\\":\\"order-taker-001\\",'
        '\\"maker_order_id\\":\\"order-maker-001\\",'
        '\\"taker_side\\":\\"BUY\\"'
        '}"'
        '}',
    )

    repositories.trades.save.assert_called_once()
    repositories.analytics.save.assert_called_once()
    repositories.positions.save.assert_called_once()
    repositories.risk.save_risk_state.assert_called_once()
    publish_sink.assert_called_once()

def test_stop_closes_owned_repositories() -> None:
    """Stopping the service should close repositories created by the service."""

    repositories = Mock()

    service = _service(settings=Settings())
    service.repositories = repositories
    service._owns_repositories = True

    service.stop()

    service.client.stop.assert_called_once()
    repositories.close.assert_called_once()
    assert service._owns_repositories is False


def test_stop_does_not_close_injected_repositories() -> None:
    """Stopping should not close repositories supplied by the caller."""

    repositories = Mock()

    service = _service(repositories=repositories)

    service.stop()

    service.client.stop.assert_called_once()
    repositories.close.assert_not_called()
