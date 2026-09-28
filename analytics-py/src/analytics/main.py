"""Application entry point for the streaming analytics service."""

from __future__ import annotations

import logging
import signal
from threading import Event, Lock
from time import perf_counter
from typing import Callable

from analytics.config.settings import Settings
from analytics.ingestion import MessageParseError, MessageParser, SocketClient
from analytics.ingestion.backpressure import BackpressureQueue, BackpressureWorker
from analytics.models import ProcessedTrade, Trade
from analytics.observability import (
    BackpressureMetrics,
    ErrorMetrics,
    PersistenceMetrics,
    ProcessingLatencyMetrics,
    RiskMetrics,
    ServiceHealthMetrics,
    ServiceMetrics,
    TradeThroughputMetrics,
    PrometheusExporter,
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
        service_metrics: ServiceMetrics | None = None,
        processing_latency_metrics: ProcessingLatencyMetrics | None = None,
        trade_throughput_metrics: TradeThroughputMetrics | None = None,
        risk_metrics: RiskMetrics | None = None,
        error_metrics: ErrorMetrics | None = None,
        health_metrics: ServiceHealthMetrics | None = None,
        prometheus_exporter: PrometheusExporter | None = None,
    ) -> None:
        self.settings = settings
        self._owns_repositories = False
        self._lifecycle_lock = Lock()
        self._started = False
        self._shutdown_complete = False

        if repositories is None and settings.database_url is not None:
            repositories = create_postgres_repositories(
                settings.database_url,
            )
            self._owns_repositories = True

        self.repositories = repositories
        self.persistence_metrics = (
            persistence_metrics or PersistenceMetrics()
        )
        self.service_metrics = service_metrics or ServiceMetrics()
        self.processing_latency_metrics = (
            processing_latency_metrics or ProcessingLatencyMetrics()
        )
        self.trade_throughput_metrics = (
            trade_throughput_metrics or TradeThroughputMetrics()
        )
        self.risk_metrics = risk_metrics or RiskMetrics()
        self.error_metrics = error_metrics or ErrorMetrics()
        self.health_metrics = health_metrics or ServiceHealthMetrics()
        self.prometheus_exporter = prometheus_exporter or PrometheusExporter(
            service_metrics=self.service_metrics,
            processing_latency_metrics=self.processing_latency_metrics,
            trade_throughput_metrics=self.trade_throughput_metrics,
            risk_metrics=self.risk_metrics,
            error_metrics=self.error_metrics,
            backpressure_metrics=self.backpressure_metrics,
            health_metrics=self.health_metrics,
            persistence_metrics=self.persistence_metrics,
            persistence_health=self.check_persistence_health,
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

    def start_metrics_server(self) -> None:
        """Start Prometheus exposition when a metrics port is configured."""
        if self.settings.metrics_port is None:
            return

        self.prometheus_exporter.start(
            port=self.settings.metrics_port,
            host=self.settings.metrics_host,
        )
        logger.info(
            "Prometheus metrics server started: %s:%d",
            self.settings.metrics_host,
            self.settings.metrics_port,
        )

    def stop_metrics_server(self) -> None:
        """Stop the Prometheus exposition server if it is running."""
        if not self.prometheus_exporter.running:
            return

        self.prometheus_exporter.stop()
        logger.info("Prometheus metrics server stopped")

    def start(self) -> None:
        """Start the analytics service exactly once until it is stopped."""
        with self._lifecycle_lock:
            if self._started:
                logger.debug("analytics service is already started")
                return

            self._started = True
            self._shutdown_complete = False

        self.health_metrics.mark_started()
        logger.info(
            "starting analytics service: engine=%s:%d",
            self.settings.engine_host,
            self.settings.engine_port,
        )

        try:
            self._message_worker.start()
            self.client.start()
        except Exception:
            try:
                self._message_worker.stop(drain=True)
            except Exception:
                logger.exception("failed to stop backpressure worker after startup failure")
            self.health_metrics.mark_stopped()
            with self._lifecycle_lock:
                self._started = False
                self._shutdown_complete = False
            logger.exception("failed to start analytics service")
            raise

    def stop(self) -> None:
        """Stop the service and clean up owned resources deterministically."""
        with self._lifecycle_lock:
            if self._shutdown_complete:
                logger.debug("analytics service is already stopped")
                return

            was_started = self._started
            self._started = False
            self._shutdown_complete = True

        if not was_started:
            logger.debug("analytics service was not started; cleaning up")

        logger.info("stopping analytics service")

        cleanup_error: Exception | None = None

        try:
            self.client.stop()
        except Exception as exc:
            cleanup_error = exc
            logger.exception("failed to stop analytics socket client")

        try:
            self._message_worker.stop(drain=True)
        except Exception as exc:
            if cleanup_error is None:
                cleanup_error = exc
            logger.exception("failed to stop backpressure worker")

        try:
            self.stop_metrics_server()
        except Exception as exc:
            if cleanup_error is None:
                cleanup_error = exc
            logger.exception("failed to stop Prometheus metrics server")

        self.health_metrics.mark_stopped()

        if self._owns_repositories and self.repositories is not None:
            repositories = self.repositories
            self._owns_repositories = False

            try:
                repositories.close()
            except Exception as exc:
                if cleanup_error is None:
                    cleanup_error = exc
                logger.exception("failed to close owned repositories")

        if cleanup_error is not None:
            raise cleanup_error

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
        """Enqueue one inbound message under bounded backpressure."""
        self.health_metrics.record_message(perf_counter())
        accepted = self._message_queue.put(
            message,
            timeout=self.settings.backpressure_enqueue_timeout,
        )
        self.backpressure_metrics.set_queue_depth(
            self._message_queue.snapshot().queue_depth,
        )
        if accepted:
            self.backpressure_metrics.record_enqueued()
            return

        self.backpressure_metrics.record_rejected()
        logger.warning("analytics inbound queue is full; rejecting message")

    def _process_queued_message(self, message: str) -> None:
        try:
            self._process_message(message)
        finally:
            self.backpressure_metrics.set_queue_depth(
                self._message_queue.snapshot().queue_depth,
            )

    def _process_message(self, message: str) -> None:
        """Parse, process, persist, and publish one queued message."""

        try:
            event = self.parser.parse(message)
        except MessageParseError as exc:
            self.service_metrics.record_parse_error()
            self.error_metrics.record_parse_error()
            logger.warning("failed to parse incoming message: %s", exc)
            return

        if isinstance(event, Trade):
            started_at = perf_counter()

            try:
                result = self.processor.process_trade_with_risk_events(
                    event,
                )

                self._persist(result)

                try:
                    self.publisher.publish(result.analytics)
                except Exception as exc:
                    self.error_metrics.record_publish_error()
                    logger.error(
                        "failed to publish analytics for trade %s: %s",
                        event.event_id,
                        exc,
                    )
                    raise

                self.service_metrics.record_published_analytics()
                self.trade_throughput_metrics.record_trade()
                self.risk_metrics.record_snapshot(
                    position=result.risk_snapshot.position,
                    realized_pnl=result.risk_snapshot.realized_pnl,
                    unrealized_pnl=result.risk_snapshot.unrealized_pnl,
                    equity=result.risk_snapshot.equity,
                    peak_equity=result.risk_snapshot.peak_equity,
                    drawdown=result.risk_snapshot.drawdown,
                )
                for risk_event in result.risk_events:
                    if risk_event.event_type == "RISK_LIMIT_WARNING":
                        self.risk_metrics.record_warning_event()
                    elif risk_event.event_type == "RISK_LIMIT_BREACHED":
                        self.risk_metrics.record_breached_event()

            except PersistenceError as exc:
                self.error_metrics.record_persistence_error()
                duration_seconds = perf_counter() - started_at
                self.service_metrics.record_trade_failure(
                    duration_seconds,
                )
                self.processing_latency_metrics.record(duration_seconds)
                logger.error(
                    "failed to persist trade %s: %s",
                    event.event_id,
                    exc,
                )

            except (TypeError, ValueError) as exc:
                self.error_metrics.record_processing_error()
                duration_seconds = perf_counter() - started_at
                self.service_metrics.record_trade_failure(
                    duration_seconds,
                )
                self.processing_latency_metrics.record(duration_seconds)
                logger.warning(
                    "failed to process trade %s: %s",
                    event.event_id,
                    exc,
                )

            else:
                duration_seconds = perf_counter() - started_at
                self.service_metrics.record_trade_success(
                    duration_seconds,
                )
                self.processing_latency_metrics.record(duration_seconds)

            return

        self.service_metrics.record_ignored_event()
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
        self.health_metrics.mark_engine_connected()
        logger.info(
            "connected to trading engine at %s:%d",
            self.settings.engine_host,
            self.settings.engine_port,
        )

    def _handle_disconnect(self) -> None:
        """Handle trading-engine disconnection."""
        self.health_metrics.mark_engine_disconnected()
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

    service.start_metrics_server()
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
