"""Application entry point for the streaming analytics service."""

from __future__ import annotations

import logging
import signal
from threading import Event
from time import perf_counter
from typing import Callable

from analytics.config.settings import Settings
from analytics.ingestion import MessageParseError, MessageParser, SocketClient
from analytics.models import ProcessedTrade, Trade
from analytics.observability import (
    PersistenceMetrics,
    check_postgres_health,
)
from analytics.persistence.errors import PersistenceError
from analytics.persistence.postgres import (
    PostgresRepositories,
    create_postgres_repositories,
)
from analytics.pipeline import AnalyticsPublisher, StreamingProcessor


logger = logging.getLogger(__name__)


class AnalyticsService:
    """Wire ingestion, processing, publishing, and optional persistence."""

    def __init__(
        self,
        settings: Settings,
        *,
        publish_sink: Callable[[str], None] | None = None,
        repositories: PostgresRepositories | None = None,
        persistence_metrics: PersistenceMetrics | None = None,
    ) -> None:
        self.settings = settings
        self._owns_repositories = False

        if repositories is None and settings.database_url is not None:
            repositories = create_postgres_repositories(
                settings.database_url,
            )
            self._owns_repositories = True

        self.repositories = repositories
        self.persistence_metrics = (
            persistence_metrics or PersistenceMetrics()
        )

        self.parser = MessageParser()
        self.processor = StreamingProcessor()

        if publish_sink is None:
            publish_sink = self._default_publish_sink

        self.publisher = AnalyticsPublisher(publish_sink)

        self.client = SocketClient(
            settings.engine_host,
            settings.engine_port,
            connect_timeout=settings.connect_timeout,
            receive_timeout=settings.receive_timeout,
            reconnect=settings.reconnect,
            reconnect_delay=settings.reconnect_delay,
            max_payload_size=settings.max_payload_size,
            on_message=self._handle_message,
            on_connect=self._handle_connect,
            on_disconnect=self._handle_disconnect,
        )

    def start(self) -> None:
        """Start the analytics service."""
        logger.info(
            "starting analytics service: engine=%s:%d",
            self.settings.engine_host,
            self.settings.engine_port,
        )

        self.client.start()

    def stop(self) -> None:
        """Stop the analytics service and owned persistence resources."""
        logger.info("stopping analytics service")
        self.client.stop()

        if self._owns_repositories and self.repositories is not None:
            self.repositories.close()
            self._owns_repositories = False

    def check_persistence_health(self) -> bool | None:
        """Check configured PostgreSQL persistence health."""
        if self.repositories is None:
            return None

        healthy = check_postgres_health(
            self.repositories.connection,
        )

        if healthy:
            logger.info("persistence health check succeeded")
        else:
            logger.error("persistence health check failed")

        return healthy


    def _handle_message(self, message: str) -> None:
        """Parse, process, persist, and publish one transport message."""
        try:
            event = self.parser.parse(message)
        except MessageParseError as exc:
            logger.warning("failed to parse incoming message: %s", exc)
            return

        if isinstance(event, Trade):
            try:
                result = self.processor.process_trade_with_risk_events(
                    event,
                )

                self._persist(result)

                self.publisher.publish(result.analytics)
            except PersistenceError as exc:
                logger.error(
                    "failed to persist trade %s: %s",
                    event.event_id,
                    exc,
                )
            except (TypeError, ValueError) as exc:
                logger.warning(
                    "failed to process trade %s: %s",
                    event.event_id,
                    exc,
                )
            return

        logger.debug(
            "ignoring %s event for current analytics pipeline",
            event.event_type,
        )

    def _persist(self, result: ProcessedTrade) -> None:
        """Persist one complete processed trade in a single transaction."""
        if self.repositories is None:
            return

        started_at = perf_counter()

        try:
            with self.repositories.connection.transaction():
                self.repositories.trades.save(result.trade)
                self.repositories.analytics.save(result.analytics)
                self.repositories.positions.save(
                    symbol=result.trade.symbol,
                    snapshot=result.risk_snapshot,
                )
                self.repositories.risk.save_risk_state(
                    symbol=result.trade.symbol,
                    snapshot=result.risk_snapshot,
                )
                for event in result.risk_events:
                    self.repositories.risk.save_event(event=event)
        except PersistenceError:
            duration_seconds = perf_counter() - started_at
            self.persistence_metrics.record_failure(duration_seconds)
            logger.error(
                "persistence failed: event_id=%s symbol=%s "
                "duration_seconds=%.6f",
                result.trade.event_id,
                result.trade.symbol,
                duration_seconds,
            )
            raise
        except Exception as exc:
            duration_seconds = perf_counter() - started_at
            self.persistence_metrics.record_failure(duration_seconds)
            logger.error(
                "persistence failed: event_id=%s symbol=%s "
                "duration_seconds=%.6f",
                result.trade.event_id,
                result.trade.symbol,
                duration_seconds,
            )
            raise PersistenceError(
                "failed to persist processed trade",
            ) from exc

        duration_seconds = perf_counter() - started_at
        self.persistence_metrics.record_success(duration_seconds)
        logger.info(
            "persistence succeeded: event_id=%s symbol=%s "
            "duration_seconds=%.6f",
            result.trade.event_id,
            result.trade.symbol,
            duration_seconds,
        )

    def _handle_connect(self) -> None:
        """Handle successful connection to the trading engine."""
        logger.info(
            "connected to trading engine at %s:%d",
            self.settings.engine_host,
            self.settings.engine_port,
        )

    def _handle_disconnect(self) -> None:
        """Handle trading-engine disconnection."""
        logger.warning("disconnected from trading engine")

    @staticmethod
    def _default_publish_sink(payload: str) -> None:
        """Log published analytics payloads until a downstream sink exists."""
        logger.info("analytics update: %s", payload)


def run(settings: Settings | None = None) -> None:
    """Run the analytics service until interrupted."""
    settings = settings or Settings.from_environment()

    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s %(levelname)s %(name)s: %(message)s",
    )

    service = AnalyticsService(settings)
    stop_event = Event()

    def _shutdown(signum: int, _frame: object) -> None:
        logger.info("received signal %d", signum)
        stop_event.set()

    signal.signal(signal.SIGINT, _shutdown)
    signal.signal(signal.SIGTERM, _shutdown)

    service.start()

    try:
        stop_event.wait()
    finally:
        service.stop()


def main() -> None:
    """CLI entry point."""
    run()


if __name__ == "__main__":
    main()
