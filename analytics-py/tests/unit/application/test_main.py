"""Tests for the analytics application service."""

from datetime import datetime, timezone
from decimal import Decimal
from unittest.mock import MagicMock, Mock

import pytest

from analytics.config.settings import Settings
from analytics.main import AnalyticsService
from analytics.observability import PersistenceMetrics
from analytics.models import (
    AnalyticsResult,
    ProcessedTrade,
    RiskEvent,
    Trade,
)
from analytics.persistence.errors import PersistenceError
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

def _transactional_repositories() -> Mock:
    """Create repository mocks with a working transaction context."""
    repositories = Mock()

    transaction = MagicMock()
    transaction.__enter__.return_value = transaction
    transaction.__exit__.return_value = False

    repositories.connection.transaction.return_value = transaction

    return repositories

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

    repositories = _transactional_repositories()
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

    repositories = _transactional_repositories()
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



def test_persist_uses_database_transaction() -> None:
    """Persistence should execute inside one database transaction."""

    repositories = _transactional_repositories()
    result = _processed_trade()
    service = _service(repositories=repositories)

    service._persist(result)

    repositories.connection.transaction.assert_called_once_with()

    transaction = repositories.connection.transaction.return_value
    transaction.__enter__.assert_called_once_with()
    transaction.__exit__.assert_called_once_with(None, None, None)


def test_persist_performs_all_writes_inside_transaction() -> None:
    """All repository writes should occur within the transaction context."""

    repositories = _transactional_repositories()
    result = _processed_trade()

    transaction = repositories.connection.transaction.return_value

    def assert_transaction_active(*_args, **_kwargs) -> None:
        assert transaction.__enter__.called
        assert not transaction.__exit__.called

    repositories.trades.save.side_effect = assert_transaction_active
    repositories.analytics.save.side_effect = assert_transaction_active
    repositories.positions.save.side_effect = assert_transaction_active
    repositories.risk.save_risk_state.side_effect = assert_transaction_active

    service = _service(repositories=repositories)
    service._persist(result)



def test_persist_wraps_failure_as_persistence_error() -> None:
    """A persistence failure should become a PersistenceError."""

    repositories = _transactional_repositories()
    result = _processed_trade()

    original_error = RuntimeError("analytics persistence failed")
    repositories.analytics.save.side_effect = original_error

    service = _service(
        settings=Settings(persistence_retry_attempts=0),
        repositories=repositories,
    )

    with pytest.raises(
        PersistenceError,
        match="failed to persist processed trade",
    ) as exc_info:
        service._persist(result)

    transaction = repositories.connection.transaction.return_value
    transaction.__enter__.assert_called_once_with()

    exit_args = transaction.__exit__.call_args.args
    assert exit_args[0] is RuntimeError
    assert exit_args[1] is original_error

    assert exc_info.value.__cause__ is original_error


def test_handle_message_does_not_publish_after_persistence_failure(
    caplog,
) -> None:
    """A failed persistence operation must not publish analytics."""

    repositories = _transactional_repositories()
    repositories.analytics.save.side_effect = RuntimeError(
        "database unavailable"
    )

    publish_sink = Mock()

    service = AnalyticsService(
        Settings(),
        repositories=repositories,
        publish_sink=publish_sink,
    )

    message = (
        '{"type":"TRADE",'
        '"request_id":"event-persistence-failure-001",'
        '"timestamp":"2026-09-27T10:00:00+00:00",'
        '"payload":"{'
        '\\"symbol\\":\\"AAPL\\",'
        '\\"price\\":\\"100\\",'
        '\\"quantity\\":8,'
        '\\"taker_order_id\\":\\"order-taker-failure\\",'
        '\\"maker_order_id\\":\\"order-maker-failure\\",'
        '\\"taker_side\\":\\"BUY\\"'
        '}"'
        '}'
    )

    with caplog.at_level("ERROR", logger="analytics.main"):
        service._handle_message(message)

    publish_sink.assert_not_called()

    assert "failed to persist trade event-persistence-failure-001" in (
        caplog.text
    )


def test_service_continues_after_persistence_failure() -> None:
    """A persistence failure must not prevent later messages from processing."""

    repositories = _transactional_repositories()

    repositories.analytics.save.side_effect = [
        RuntimeError("temporary database failure"),
        None,
        None,
    ]

    publish_sink = Mock()

    service = AnalyticsService(
        Settings(persistence_retry_attempts=1),
        repositories=repositories,
        publish_sink=publish_sink,
    )

    first_message = (
        '{"type":"TRADE",'
        '"request_id":"event-failure-001",'
        '"timestamp":"2026-09-27T10:00:00+00:00",'
        '"payload":"{'
        '\\"symbol\\":\\"AAPL\\",'
        '\\"price\\":\\"100\\",'
        '\\"quantity\\":8,'
        '\\"taker_order_id\\":\\"order-taker-001\\",'
        '\\"maker_order_id\\":\\"order-maker-001\\",'
        '\\"taker_side\\":\\"BUY\\"'
        '}"'
        '}'
    )

    second_message = (
        '{"type":"TRADE",'
        '"request_id":"event-success-002",'
        '"timestamp":"2026-09-27T10:01:00+00:00",'
        '"payload":"{'
        '\\"symbol\\":\\"MSFT\\",'
        '\\"price\\":\\"200\\",'
        '\\"quantity\\":5,'
        '\\"taker_order_id\\":\\"order-taker-002\\",'
        '\\"maker_order_id\\":\\"order-maker-002\\",'
        '\\"taker_side\\":\\"BUY\\"'
        '}"'
        '}'
    )

    service._handle_message(first_message)
    service._handle_message(second_message)

    assert repositories.analytics.save.call_count == 3
    assert publish_sink.call_count == 2

def test_handle_message_persists_and_publishes_trade() -> None:
    """A valid trade should be persisted before its analytics are published."""

    repositories = _transactional_repositories()
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


def test_check_persistence_health_returns_none_when_disabled() -> None:
    """Health should be unknown when PostgreSQL persistence is disabled."""

    service = _service()

    assert service.check_persistence_health() is None


def test_check_persistence_health_returns_true_when_postgres_is_healthy(
    monkeypatch,
) -> None:
    """Health should report a healthy configured PostgreSQL connection."""

    repositories = Mock()
    monkeypatch.setattr(
        "analytics.main.check_postgres_health",
        Mock(return_value=True),
    )

    service = _service(repositories=repositories)

    assert service.check_persistence_health() is True


def test_check_persistence_health_returns_false_when_postgres_is_unhealthy(
    monkeypatch,
) -> None:
    """Health should report an unhealthy configured PostgreSQL connection."""

    repositories = Mock()
    monkeypatch.setattr(
        "analytics.main.check_postgres_health",
        Mock(return_value=False),
    )

    service = _service(repositories=repositories)

    assert service.check_persistence_health() is False


def test_persist_records_success_metrics() -> None:
    """Successful persistence should update success metrics."""

    repositories = _transactional_repositories()
    metrics = PersistenceMetrics()
    result = _processed_trade()

    service = AnalyticsService(
        Settings(),
        repositories=repositories,
        persistence_metrics=metrics,
    )

    service._persist(result)

    snapshot = metrics.snapshot()

    assert snapshot.success_count == 1
    assert snapshot.failure_count == 0
    assert snapshot.total_duration_seconds > 0.0


def test_persist_records_failure_metrics() -> None:
    """Failed persistence should update failure metrics."""

    repositories = _transactional_repositories()
    metrics = PersistenceMetrics()
    result = _processed_trade()

    original_error = RuntimeError("database unavailable")
    repositories.analytics.save.side_effect = original_error

    service = AnalyticsService(
        Settings(persistence_retry_attempts=0),
        repositories=repositories,
        persistence_metrics=metrics,
    )

    with pytest.raises(
        PersistenceError,
        match="failed to persist processed trade",
    ):
        service._persist(result)

    snapshot = metrics.snapshot()

    assert snapshot.success_count == 0
    assert snapshot.failure_count == 1
    assert snapshot.total_duration_seconds > 0.0


def test_persist_records_success_and_failure_separately() -> None:
    """Successes and failures should be tracked independently."""

    repositories = _transactional_repositories()
    metrics = PersistenceMetrics()
    result = _processed_trade()

    repositories.analytics.save.side_effect = [
        RuntimeError("temporary database failure"),
        None,
    ]

    service = AnalyticsService(
        Settings(persistence_retry_attempts=0),
        repositories=repositories,
        persistence_metrics=metrics,
    )

    with pytest.raises(
        PersistenceError,
        match="failed to persist processed trade",
    ):
        service._persist(result)

    service._persist(result)

    snapshot = metrics.snapshot()

    assert snapshot.success_count == 1
    assert snapshot.failure_count == 1
    assert snapshot.operation_count == 2
    assert snapshot.total_duration_seconds > 0.0


def test_persist_logs_success_context(
    caplog: pytest.LogCaptureFixture,
) -> None:
    """Successful persistence should log event context and duration."""

    repositories = _transactional_repositories()
    metrics = PersistenceMetrics()
    result = _processed_trade()

    service = AnalyticsService(
        Settings(),
        repositories=repositories,
        persistence_metrics=metrics,
    )

    with caplog.at_level("INFO", logger="analytics.main"):
        service._persist(result)

    assert "persistence succeeded:" in caplog.text
    assert f"event_id={result.trade.event_id}" in caplog.text
    assert f"symbol={result.trade.symbol}" in caplog.text
    assert "duration_seconds=" in caplog.text


def test_persist_logs_failure_context(
    caplog: pytest.LogCaptureFixture,
) -> None:
    """Failed persistence should log event context and duration."""

    repositories = _transactional_repositories()
    metrics = PersistenceMetrics()
    result = _processed_trade()

    repositories.analytics.save.side_effect = RuntimeError(
        "database unavailable",
    )

    service = AnalyticsService(
        Settings(persistence_retry_attempts=0),
        repositories=repositories,
        persistence_metrics=metrics,
    )

    with caplog.at_level("ERROR", logger="analytics.main"):
        with pytest.raises(
            PersistenceError,
            match="failed to persist processed trade",
        ):
            service._persist(result)

    assert "persistence failed after 1 attempts:" in caplog.text
    assert f"event_id={result.trade.event_id}" in caplog.text
    assert f"symbol={result.trade.symbol}" in caplog.text
    assert "duration_seconds=" in caplog.text


def test_service_metrics_can_be_injected() -> None:
    """The service should use caller-provided service metrics."""

    from analytics.observability import ServiceMetrics

    metrics = ServiceMetrics()


    service = AnalyticsService(
        Settings(),
        publish_sink=Mock(),
        service_metrics=metrics,
    )

    assert service.service_metrics is metrics


def test_parse_error_updates_service_metrics() -> None:
    """Malformed messages should increment the parse error counter."""

    from analytics.observability import ServiceMetrics

    metrics = ServiceMetrics()
    service = AnalyticsService(
        Settings(),
        publish_sink=Mock(),
        service_metrics=metrics,
    )

    service._handle_message("{not-valid-json")

    snapshot = metrics.snapshot()

    assert snapshot.parse_error_count == 1
    assert snapshot.trade_attempt_count == 0
    assert snapshot.published_analytics_count == 0


def test_ignored_event_updates_service_metrics() -> None:
    """Valid non-trade events should increment the ignored counter."""

    from analytics.observability import ServiceMetrics

    metrics = ServiceMetrics()
    service = AnalyticsService(
        Settings(),
        publish_sink=Mock(),
        service_metrics=metrics,
    )

    service._handle_message(
        '{"type":"MARKET_TICK",'
        '"request_id":"tick-001",'
        '"timestamp":"2026-09-27T10:00:00+00:00",'
        '"payload":"{'
        '\\"symbol\\":\\"BTCUSD\\",'
        '\\"price\\":\\"100.00\\",'
        '\\"quantity\\":1'
        '}"}',
    )

    snapshot = metrics.snapshot()

    assert snapshot.ignored_event_count == 1
    assert snapshot.trade_attempt_count == 0


def test_successful_trade_updates_service_metrics() -> None:
    """A successful trade should update processing and publish metrics."""

    from analytics.observability import ServiceMetrics

    metrics = ServiceMetrics()
    publish_sink = Mock()

    service = AnalyticsService(
        Settings(),
        publish_sink=publish_sink,
        service_metrics=metrics,
    )

    service._handle_message(
        '{"type":"TRADE",'
        '"request_id":"event-metrics-001",'
        '"timestamp":"2026-09-27T10:00:00+00:00",'
        '"payload":"{'
        '\\"symbol\\":\\"AAPL\\",'
        '\\"price\\":\\"100\\",'
        '\\"quantity\\":8,'
        '\\"taker_order_id\\":\\"order-taker-metrics-001\\",'
        '\\"maker_order_id\\":\\"order-maker-metrics-001\\",'
        '\\"taker_side\\":\\"BUY\\"'
        '}"'
        '}',
    )

    snapshot = metrics.snapshot()

    assert snapshot.processed_trade_count == 1
    assert snapshot.processing_failure_count == 0
    assert snapshot.published_analytics_count == 1
    assert snapshot.trade_attempt_count == 1
    assert snapshot.total_processing_duration_seconds > 0.0
    assert snapshot.average_processing_duration_seconds > 0.0


def test_persistence_failure_updates_service_failure_metrics() -> None:
    """A persistence failure should count as a failed trade pipeline."""

    from analytics.observability import ServiceMetrics

    repositories = _transactional_repositories()
    repositories.analytics.save.side_effect = RuntimeError(
        "database unavailable",
    )

    metrics = ServiceMetrics()
    publish_sink = Mock()

    service = AnalyticsService(
        Settings(),
        repositories=repositories,
        publish_sink=publish_sink,
        service_metrics=metrics,
    )

    service._handle_message(
        '{"type":"TRADE",'
        '"request_id":"event-metrics-failure-001",'
        '"timestamp":"2026-09-27T10:00:00+00:00",'
        '"payload":"{'
        '\\"symbol\\":\\"AAPL\\",'
        '\\"price\\":\\"100\\",'
        '\\"quantity\\":8,'
        '\\"taker_order_id\\":\\"order-taker-metrics-failure\\",'
        '\\"maker_order_id\\":\\"order-maker-metrics-failure\\",'
        '\\"taker_side\\":\\"BUY\\"'
        '}"'
        '}',
    )

    snapshot = metrics.snapshot()

    assert snapshot.processed_trade_count == 0
    assert snapshot.processing_failure_count == 1
    assert snapshot.published_analytics_count == 0
    assert snapshot.trade_attempt_count == 1
    assert snapshot.total_processing_duration_seconds > 0.0
