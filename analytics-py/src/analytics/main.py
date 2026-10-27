"""Application entry point for the streaming analytics service."""

from __future__ import annotations

import logging
import signal
from concurrent.futures import Future
from dataclasses import dataclass
from threading import Event, Lock
from time import perf_counter, sleep
from typing import Callable

from analytics.config.settings import Settings
from analytics.ingestion import MessageParseError, MessageParser
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
    configure_logging,
)
from analytics.persistence.errors import PersistenceError
from analytics.persistence.postgres import (
    PostgresRepositories,
    create_postgres_repositories,
)
from analytics.integration.gateway_receiver import GatewayAnalyticsReceiver
from analytics.pipeline import AnalyticsPublisher, StreamingProcessor


logger = logging.getLogger(__name__)


@dataclass(slots=True)
class _QueuedAnalyticsMessage:
    """A message plus the completion signal used by the gateway ACK path."""

    payload: str
    completion: Future[bool | None]


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
        self._persistence_lock = Lock()
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
        self.backpressure_metrics = BackpressureMetrics()
        self.health_metrics = health_metrics or ServiceHealthMetrics()

        self.parser = MessageParser()
        self.processor = StreamingProcessor(risk_limits=settings.risk_limit_config)
        self._completed_trade_ids: set[str] = set()

        self._message_queue: BackpressureQueue[_QueuedAnalyticsMessage] = BackpressureQueue(
            capacity=settings.backpressure_queue_capacity,
        )
        self._message_worker = BackpressureWorker(
            self._message_queue,
            self._process_queued_message,
        )

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

        # Keep the public attribute name stable for service callers/tests while
        # replacing direct engine ingestion with the Phase 4.6 Gateway receiver.
        self.client = GatewayAnalyticsReceiver(
            settings.gateway_host,
            settings.gateway_port,
            max_payload_size=settings.max_payload_size,
            on_message=self._handle_message,
            on_connect=self._handle_connect,
            on_disconnect=self._handle_disconnect,
        )

        if publish_sink is None:
            publish_sink = self._publish_to_gateway

        self.publisher = AnalyticsPublisher(
            publish_sink,
            retry_attempts=settings.publish_retry_attempts,
            retry_delay=settings.publish_retry_delay,
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
                logger.debug("service_start_ignored reason=already_started")
                return

            self._started = True
            self._shutdown_complete = False

        self.health_metrics.mark_started()
        logger.info(
            "service_start gateway_host=%s gateway_port=%d",
            self.settings.gateway_host,
            self.settings.gateway_port,
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
                logger.debug("service_stop_ignored reason=already_stopped")
                return

            was_started = self._started
            self._started = False
            self._shutdown_complete = True

        if not was_started:
            logger.debug("service_stop_cleanup reason=service_not_started")

        logger.info("service_stop")

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
        """Check PostgreSQL health and recover owned connections when possible."""
        with self._persistence_lock:
            if self.repositories is None:
                return None

            if check_postgres_health(self.repositories.connection):
                logger.info("persistence health check succeeded")
                return True

            logger.error("persistence health check failed")

            # Injected repositories belong to the caller; never replace or close
            # their connections behind the caller's back.
            if not self._owns_repositories or not self.settings.database_url:
                return False

            try:
                replacement = create_postgres_repositories(
                    self.settings.database_url,
                )
            except Exception as exc:
                logger.error(
                    "persistence_connection_recovery_failed error_type=%s",
                    type(exc).__name__,
                )
                return False

            if not check_postgres_health(replacement.connection):
                try:
                    replacement.close()
                except Exception:
                    logger.exception(
                        "failed to close unhealthy replacement PostgreSQL connection"
                    )
                logger.error("persistence_connection_recovery_failed reason=health_check")
                return False

            previous = self.repositories
            self.repositories = replacement
            try:
                previous.close()
            except Exception:
                logger.exception(
                    "failed to close replaced PostgreSQL repositories"
                )

            logger.info("persistence_connection_recovered")
            return True

    def _handle_message(self, message: str) -> bool | None:
        """Handle one inbound message with lifecycle-aware backpressure."""
        self.health_metrics.record_message(perf_counter())

        # Direct calls before service startup retain the established synchronous
        # contract used by tests and internal callers. SocketClient invokes this
        # callback only after service.start(), so live traffic uses the bounded
        # queue and dedicated worker below.
        if not self._started:
            return self._process_message(message)

        completion: Future[bool | None] = Future()
        work_item = _QueuedAnalyticsMessage(message, completion)
        accepted = self._message_queue.put(
            work_item,
            timeout=self.settings.backpressure_enqueue_timeout,
        )
        self.backpressure_metrics.set_queue_depth(
            self._message_queue.snapshot().queue_depth,
        )
        if accepted:
            self.backpressure_metrics.record_enqueued()
            # Wait for the worker's final result; queue admission alone is not
            # a persistence acknowledgement.
            return completion.result()

        self.backpressure_metrics.record_rejected()
        logger.warning(
            "backpressure_message_rejected queue_depth=%d queue_capacity=%d",
            self._message_queue.snapshot().queue_depth,
            self.settings.backpressure_queue_capacity,
        )
        return False

    def _process_queued_message(self, work_item: _QueuedAnalyticsMessage) -> None:
        try:
            outcome = self._process_message(work_item.payload)
            work_item.completion.set_result(outcome)
        except Exception as exc:
            if not work_item.completion.done():
                work_item.completion.set_exception(exc)
            raise
        finally:
            self.backpressure_metrics.set_queue_depth(
                self._message_queue.snapshot().queue_depth,
            )

    def _process_message(self, message: str) -> bool | None:
        """Parse, process, persist, and publish one queued message."""

        try:
            event = self.parser.parse(message)
        except MessageParseError as exc:
            self.service_metrics.record_parse_error()
            self.error_metrics.record_parse_error()
            logger.warning("message_parse_failed error=%s", exc)
            return False

        if isinstance(event, Trade):
            started_at = perf_counter()

            try:
                if (
                    not self.processor.has_processed_trade(event.trade_id)
                    and self.processor.is_late_trade(event)
                ):
                    results = self._reconcile_history(incoming_trade=event)
                    self._completed_trade_ids.update(
                        result.trade.trade_id for result in results
                    )
                    self.trade_throughput_metrics.record_trade()
                    duration_seconds = perf_counter() - started_at
                    self.service_metrics.record_trade_success(duration_seconds)
                    self.processing_latency_metrics.record(duration_seconds)
                    logger.info(
                        "chronological_reconciliation_completed trade_id=%s replayed_trades=%d",
                        event.trade_id,
                        len(results),
                    )
                    return self.repositories is not None

                result = self.processor.process_trade_with_risk_events(
                    event,
                )

                if (
                    getattr(result, "trade", event) is not event
                    and event.trade_id in self._completed_trade_ids
                ):
                    logger.info(
                        "duplicate_trade_skipped trade_id=%s event_id=%s",
                        event.trade_id,
                        event.event_id,
                    )
                    return self.repositories is not None

                self._persist(result)
                persisted = self.repositories is not None
                # Persistence is the durable boundary. Mark the trade complete
                # before publishing so a retry after a publish/socket failure
                # cannot re-apply its risk and position effects in memory.
                self._completed_trade_ids.add(event.trade_id)

                try:
                    self.publisher.publish(result.analytics)
                except Exception as exc:
                    self.error_metrics.record_publish_error()
                    logger.error(
                        "analytics_publish_failed event_id=%s symbol=%s error=%s",
                        event.event_id,
                        event.symbol,
                        exc,
                    )
                    raise

                self.service_metrics.record_published_analytics()
                for risk_event in result.risk_events:
                    try:
                        self.publisher.publish_risk_event(risk_event)
                    except Exception as exc:
                        self.error_metrics.record_publish_error()
                        logger.error(
                            "risk_event_publish_failed event_id=%s symbol=%s error=%s",
                            risk_event.event_id,
                            risk_event.symbol,
                            exc,
                        )
                        raise
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
                    "trade_pipeline_persistence_failed event_id=%s symbol=%s error=%s",
                    event.event_id,
                    event.symbol,
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
                    "trade_processing_failed event_id=%s symbol=%s error=%s",
                    event.event_id,
                    event.symbol,
                    exc,
                )

            else:
                duration_seconds = perf_counter() - started_at
                self.service_metrics.record_trade_success(
                    duration_seconds,
                )
                self.processing_latency_metrics.record(duration_seconds)
                return persisted

            return False

        self.service_metrics.record_ignored_event()
        logger.debug(
            "ignoring %s event for current analytics pipeline",
            event.event_type,
        )

    def _persist(self, result: ProcessedTrade) -> None:
        """Persist a processed trade while coordinating connection recovery."""
        with self._persistence_lock:
            self._persist_with_retries(result)

    def _persist_with_retries(self, result: ProcessedTrade) -> None:
        """Persist one complete processed trade in a single transaction."""
        if self.repositories is None:
            return

        started_at = perf_counter()
        attempts = self.settings.persistence_retry_attempts + 1

        for attempt in range(attempts):
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
            except PersistenceError as exc:
                duration_seconds = perf_counter() - started_at
                self.persistence_metrics.record_failure(duration_seconds)
                if attempt >= self.settings.persistence_retry_attempts:
                    logger.error(
                        "persistence_failed attempts=%d event_id=%s symbol=%s "
                        "duration_seconds=%.6f error=%s",
                        attempt + 1,
                        result.trade.event_id,
                        result.trade.symbol,
                        duration_seconds,
                        exc,
                    )
                    raise
                logger.warning(
                    "persistence_retry attempt=%d total_attempts=%d "
                    "event_id=%s symbol=%s error=%s",
                    attempt + 1,
                    attempts,
                    result.trade.event_id,
                    result.trade.symbol,
                    exc,
                )
            except Exception as exc:
                duration_seconds = perf_counter() - started_at
                self.persistence_metrics.record_failure(duration_seconds)
                wrapped = PersistenceError("failed to persist processed trade")
                if attempt >= self.settings.persistence_retry_attempts:
                    logger.error(
                        "persistence_failed attempts=%d event_id=%s symbol=%s "
                        "duration_seconds=%.6f error=%s",
                        attempt + 1,
                        result.trade.event_id,
                        result.trade.symbol,
                        duration_seconds,
                        exc,
                    )
                    raise wrapped from exc
                logger.warning(
                    "persistence_retry attempt=%d total_attempts=%d "
                    "event_id=%s symbol=%s error=%s",
                    attempt + 1,
                    attempts,
                    result.trade.event_id,
                    result.trade.symbol,
                    exc,
                )
            else:
                duration_seconds = perf_counter() - started_at
                self.persistence_metrics.record_success(duration_seconds)
                logger.info(
                    "persistence_succeeded event_id=%s symbol=%s "
                    "attempt=%d duration_seconds=%.6f",
                    result.trade.event_id,
                    result.trade.symbol,
                    attempt + 1,
                    duration_seconds,
                )
                return

            if self.settings.persistence_retry_delay:
                sleep(self.settings.persistence_retry_delay)

        raise AssertionError("persistence retry loop exited unexpectedly")

    def _reconcile_history(
        self,
        *,
        incoming_trade: Trade | None = None,
    ) -> tuple[ProcessedTrade, ...]:
        """Rebuild derived persistence from authoritative trades atomically.

        The trades table is never cleared. Analytics, position/risk snapshots,
        and risk events are replaced in one transaction so stale derived rows
        from a previous arrival order cannot survive a recovery.
        """
        if self.repositories is None:
            known = [result.trade for result in self.processor.processed_results()]
            if incoming_trade is not None:
                known.append(incoming_trade)
            results = self.processor.replay_trades(known)
        else:
            with self._persistence_lock:
                history_before = self.repositories.trades.list_all()
                try:
                    with self.repositories.connection.transaction():
                        existing_ids = {trade.trade_id for trade in history_before}
                        if (
                            incoming_trade is not None
                            and incoming_trade.trade_id not in existing_ids
                        ):
                            self.repositories.trades.save(incoming_trade)

                        history = self.repositories.trades.list_all()
                        results = self.processor.replay_trades(history)
                        with self.repositories.connection.cursor() as cursor:
                            cursor.execute("DELETE FROM risk_events")
                            cursor.execute("DELETE FROM analytics_results")
                            cursor.execute("DELETE FROM positions")
                            cursor.execute("DELETE FROM risk_state")

                        for result in results:
                            self.repositories.analytics.save(result.analytics)
                            self.repositories.positions.save(
                                symbol=result.trade.symbol,
                                snapshot=result.risk_snapshot,
                            )
                            self.repositories.risk.save_risk_state(
                                symbol=result.trade.symbol,
                                snapshot=result.risk_snapshot,
                            )
                            for risk_event in result.risk_events:
                                self.repositories.risk.save_event(event=risk_event)
                except Exception:
                    # Restore in-memory state to the last committed history if
                    # the transaction fails; the database transaction rolls back.
                    self.processor.replay_trades(history_before)
                    raise

        self._completed_trade_ids = {
            result.trade.trade_id for result in results
        }
        latest_by_symbol: dict[str, ProcessedTrade] = {}
        for result in results:
            latest_by_symbol[result.trade.symbol] = result

        for result in latest_by_symbol.values():
            try:
                self.publisher.publish(result.analytics)
            except Exception as exc:
                self.error_metrics.record_publish_error()
                logger.error(
                    "analytics_recovery_publish_failed event_id=%s symbol=%s error=%s",
                    result.analytics.event_id,
                    result.trade.symbol,
                    exc,
                )
                raise

        logger.info(
            "chronological_history_reconciled trades=%d symbols=%d",
            len(results),
            len(latest_by_symbol),
        )
        return results

    def _handle_connect(self) -> None:
        """Replay authoritative trade history and reconcile derived state."""
        self.health_metrics.mark_engine_connected()
        logger.info(
            "gateway_connected host=%s port=%d",
            self.settings.gateway_host,
            self.settings.gateway_port,
        )

        if self.repositories is None:
            return

        try:
            self._reconcile_history()
        except Exception:
            # A replay failure must not tear down the receiver or analytics service.
            logger.exception("analytics_history_reconciliation_failed")

    def _handle_disconnect(self) -> None:
        """Handle Gateway disconnection."""
        self.health_metrics.mark_engine_disconnected()
        logger.warning(
            "gateway_disconnected host=%s port=%d",
            self.settings.gateway_host,
            self.settings.gateway_port,
        )

    def _publish_to_gateway(self, payload: str) -> None:
        """Publish a versioned analytics payload over the active Gateway socket."""
        self.client.send(payload)

    def _default_publish_sink(payload: str) -> None:
        """Log published analytics payloads until a downstream sink exists."""
        logger.info("analytics update: %s", payload)


def run(settings: Settings | None = None) -> None:
    """Run the analytics service until interrupted."""
    settings = settings or Settings.from_environment()

    configure_logging(
        level=settings.log_level,
        log_format=settings.log_format,
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
