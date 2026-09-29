"""Failure-recovery tests for persistence and publishing."""

from datetime import datetime, timezone
from decimal import Decimal

from analytics.config.settings import Settings
from analytics.main import AnalyticsService
from analytics.models import AnalyticsResult, Trade
from analytics.persistence.postgres import PostgresRepositories
from analytics.pipeline import AnalyticsPublisher, StreamingProcessor


class _Transaction:
    def __init__(self, owner: "_Connection") -> None:
        self.owner = owner

    def __enter__(self) -> "_Transaction":
        self.owner.transactions += 1
        return self

    def __exit__(self, exc_type, exc, tb) -> bool:
        if exc_type is not None:
            self.owner.rollbacks += 1
        else:
            self.owner.commits += 1
        return False


class _Connection:
    def __init__(self) -> None:
        self.transactions = 0
        self.commits = 0
        self.rollbacks = 0

    def transaction(self) -> _Transaction:
        return _Transaction(self)


class _Repository:
    def __init__(self, connection: _Connection, fail_first: bool = False) -> None:
        self.connection = connection
        self.calls = 0
        self.fail_first = fail_first


class _TradeRepository(_Repository):
    def save(self, trade: Trade) -> None:
        self.calls += 1
        if self.fail_first and self.calls == 1:
            raise RuntimeError("temporary database failure")


class _RecordingRepository(_Repository):
    def save(self, *args, **kwargs) -> None:
        self.calls += 1


class _RiskRepository(_Repository):
    def save_risk_state(self, **kwargs) -> None:
        self.calls += 1

    def save_event(self, **kwargs) -> None:
        self.calls += 1


def _repositories(connection: _Connection) -> PostgresRepositories:
    return PostgresRepositories(
        connection=connection,
        trades=_TradeRepository(connection, fail_first=True),
        analytics=_RecordingRepository(connection),
        positions=_RecordingRepository(connection),
        risk=_RiskRepository(connection),
    )


def _trade() -> Trade:
    return Trade(
        event_id="trade-recovery-001",
        trade_id="trade-001",
        event_type="TRADE",
        symbol="SIM",
        price=Decimal("101.25"),
        quantity=10,
        taker_side="BUY",
        buy_order_id="buy-001",
        sell_order_id="sell-001",
        timestamp=datetime(2026, 9, 12, 18, 30, tzinfo=timezone.utc),
    )


def test_persistence_retry_reuses_transaction_boundary_without_replaying_publish() -> None:
    connection = _Connection()
    service = AnalyticsService(
        Settings(
            persistence_retry_attempts=1,
            persistence_retry_delay=0,
        ),
        repositories=_repositories(connection),
    )

    result = StreamingProcessor().process_trade_with_risk_events(_trade())
    published: list[str] = []
    service.publisher = AnalyticsPublisher(published.append)

    service._persist(result)

    assert connection.transactions == 2
    assert connection.rollbacks == 1
    assert connection.commits == 1
    assert service.repositories.trades.calls == 2


def test_publisher_retry_retries_only_publish_after_persistence() -> None:
    connection = _Connection()
    repositories = _repositories(connection)
    # Build a fresh repository set whose trade repository succeeds immediately.
    repositories = PostgresRepositories(
        connection=connection,
        trades=_TradeRepository(connection),
        analytics=_RecordingRepository(connection),
        positions=_RecordingRepository(connection),
        risk=_RiskRepository(connection),
    )

    attempts = 0
    published: list[str] = []

    def sink(payload: str) -> None:
        nonlocal attempts
        attempts += 1
        if attempts == 1:
            raise RuntimeError("temporary downstream failure")
        published.append(payload)

    service = AnalyticsService(
        Settings(
            persistence_retry_attempts=0,
            publish_retry_attempts=1,
            publish_retry_delay=0,
        ),
        repositories=repositories,
        publish_sink=sink,
    )

    service._process_message(
        ('{"type":"TRADE",'
        '"request_id":"trade-recovery-002",'
        '"timestamp":"2026-09-12T18:30:00+00:00",'
        '"payload":"{'
        '\\\"symbol\\":\\\"SIM\\",'
        '\\\"price\\":\\\"101.25\\",'
        '\\\"quantity\\":10,'
        '\\\"taker_order_id\\":\\\"buy-002\\",'
        '\\\"maker_order_id\\":\\\"sell-002\\",'
        '\\\"taker_side\\":\\\"BUY\\\"'
        '}"'
        '}')
    )

    assert attempts == 2
    assert len(published) == 1
    assert connection.transactions == 1
    assert connection.commits == 1
    assert repositories.trades.calls == 1
    assert service.error_metrics.snapshot().publish_error_count == 0
