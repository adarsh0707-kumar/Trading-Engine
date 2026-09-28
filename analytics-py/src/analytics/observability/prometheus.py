"""Prometheus exposition for analytics service metrics."""

from __future__ import annotations

from threading import Lock
from typing import Callable

from prometheus_client import CollectorRegistry, start_http_server
from prometheus_client.core import (
    CounterMetricFamily,
    GaugeMetricFamily,
    SummaryMetricFamily,
)
from prometheus_client.registry import Collector

from analytics.observability.backpressure import BackpressureMetrics
from analytics.observability.health_metrics import ServiceHealthMetrics
from analytics.observability.metrics import (
    ErrorMetrics,
    PersistenceMetrics,
    ProcessingLatencyMetrics,
    RiskMetrics,
    ServiceMetrics,
    TradeThroughputMetrics,
)


class AnalyticsPrometheusCollector(Collector):
    """Expose in-memory analytics metrics as Prometheus metric families."""

    def __init__(
        self,
        *,
        service_metrics: ServiceMetrics,
        processing_latency_metrics: ProcessingLatencyMetrics,
        trade_throughput_metrics: TradeThroughputMetrics,
        risk_metrics: RiskMetrics,
        error_metrics: ErrorMetrics,
        persistence_metrics: PersistenceMetrics,
        health_metrics: ServiceHealthMetrics | None = None,
        persistence_health: Callable[[], bool | None] | None = None,
    ) -> None:
        self._service_metrics = service_metrics
        self._processing_latency_metrics = processing_latency_metrics
        self._trade_throughput_metrics = trade_throughput_metrics
        self._risk_metrics = risk_metrics
        self._error_metrics = error_metrics
        self._backpressure_metrics = backpressure_metrics
        self._persistence_metrics = persistence_metrics
        self._health_metrics = health_metrics
        self._persistence_health = persistence_health

    def collect(self):
        service = self._service_metrics.snapshot()
        yield CounterMetricFamily(
            "trading_engine_analytics_processed_trades_total",
            "Total number of successfully processed trades.",
            value=service.processed_trade_count,
        )
        yield CounterMetricFamily(
            "trading_engine_analytics_processing_failures_total",
            "Total number of failed trade-processing attempts.",
            value=service.processing_failure_count,
        )
        yield CounterMetricFamily(
            "trading_engine_analytics_parse_errors_total",
            "Total number of incoming messages rejected by the parser.",
            value=service.parse_error_count,
        )
        yield CounterMetricFamily(
            "trading_engine_analytics_ignored_events_total",
            "Total number of valid events ignored by the analytics pipeline.",
            value=service.ignored_event_count,
        )
        yield CounterMetricFamily(
            "trading_engine_analytics_published_analytics_total",
            "Total number of analytics results handed to the publisher.",
            value=service.published_analytics_count,
        )
        yield SummaryMetricFamily(
            "trading_engine_analytics_processing_duration_seconds",
            "Trade pipeline processing duration.",
            count_value=service.trade_attempt_count,
            sum_value=service.total_processing_duration_seconds,
        )
        yield GaugeMetricFamily(
            "trading_engine_analytics_average_processing_duration_seconds",
            "Average trade pipeline processing duration.",
            value=service.average_processing_duration_seconds,
        )

        latency = self._processing_latency_metrics.snapshot()
        yield SummaryMetricFamily(
            "trading_engine_analytics_processing_latency_seconds",
            "Observed trade processing latency.",
            count_value=latency.sample_count,
            sum_value=latency.total_duration_seconds,
        )
        yield GaugeMetricFamily(
            "trading_engine_analytics_processing_latency_min_seconds",
            "Minimum observed trade processing latency.",
            value=latency.min_duration_seconds or 0.0,
        )
        yield GaugeMetricFamily(
            "trading_engine_analytics_processing_latency_max_seconds",
            "Maximum observed trade processing latency.",
            value=latency.max_duration_seconds or 0.0,
        )
        yield GaugeMetricFamily(
            "trading_engine_analytics_processing_latency_p50_seconds",
            "P50 observed trade processing latency.",
            value=latency.p50_duration_seconds or 0.0,
        )
        yield GaugeMetricFamily(
            "trading_engine_analytics_processing_latency_p95_seconds",
            "P95 observed trade processing latency.",
            value=latency.p95_duration_seconds or 0.0,
        )
        yield GaugeMetricFamily(
            "trading_engine_analytics_processing_latency_p99_seconds",
            "P99 observed trade processing latency.",
            value=latency.p99_duration_seconds or 0.0,
        )

        throughput = self._trade_throughput_metrics.snapshot()
        yield GaugeMetricFamily(
            "trading_engine_analytics_trades_per_second",
            "Successfully processed trades per second in the configured window.",
            value=throughput.trades_per_second,
        )
        yield GaugeMetricFamily(
            "trading_engine_analytics_window_trade_count",
            "Successfully processed trades in the configured throughput window.",
            value=throughput.trade_count,
        )
        yield CounterMetricFamily(
            "trading_engine_analytics_trades_total",
            "Total successfully processed trades.",
            value=throughput.total_trade_count,
        )

        risk = self._risk_metrics.snapshot()
        yield GaugeMetricFamily(
            "trading_engine_analytics_position",
            "Current portfolio position.",
            value=risk.current_position,
        )
        yield GaugeMetricFamily(
            "trading_engine_analytics_max_abs_position",
            "Maximum absolute portfolio position observed.",
            value=risk.max_abs_position,
        )
        yield GaugeMetricFamily(
            "trading_engine_analytics_realized_pnl",
            "Current realized P&L.",
            value=float(risk.current_realized_pnl),
        )
        yield GaugeMetricFamily(
            "trading_engine_analytics_unrealized_pnl",
            "Current unrealized P&L.",
            value=float(risk.current_unrealized_pnl),
        )
        yield GaugeMetricFamily(
            "trading_engine_analytics_equity",
            "Current portfolio equity.",
            value=float(risk.current_equity),
        )
        yield GaugeMetricFamily(
            "trading_engine_analytics_peak_equity",
            "Peak portfolio equity.",
            value=float(risk.peak_equity),
        )
        yield GaugeMetricFamily(
            "trading_engine_analytics_drawdown",
            "Current portfolio drawdown.",
            value=float(risk.current_drawdown),
        )
        yield GaugeMetricFamily(
            "trading_engine_analytics_max_drawdown",
            "Maximum portfolio drawdown observed.",
            value=float(risk.max_drawdown),
        )
        yield CounterMetricFamily(
            "trading_engine_analytics_risk_warnings_total",
            "Total risk-limit warning events.",
            value=risk.warning_event_count,
        )
        yield CounterMetricFamily(
            "trading_engine_analytics_risk_breaches_total",
            "Total risk-limit breach events.",
            value=risk.breached_event_count,
        )

        if self._backpressure_metrics is not None:
            backpressure = self._backpressure_metrics.snapshot()
            yield GaugeMetricFamily(
                "trading_engine_analytics_backpressure_queue_depth",
                "Current inbound analytics queue depth.",
                value=backpressure.queue_depth,
            )
            yield CounterMetricFamily(
                "trading_engine_analytics_backpressure_enqueued_total",
                "Total inbound messages accepted by the bounded queue.",
                value=backpressure.enqueued_count,
            )
            yield GaugeMetricFamily(
                "trading_engine_analytics_backpressure_rejected_total",
                "Total inbound messages rejected because the queue was full.",
                value=backpressure.rejected_count,
            )

        errors = self._error_metrics.snapshot()
        yield self._error_family(errors)

        persistence = self._persistence_metrics.snapshot()
        yield self._persistence_family(persistence)

        if self._health_metrics is not None:
            health = self._health_metrics.snapshot()
            yield GaugeMetricFamily(
                "trading_engine_analytics_service_live",
                "Analytics service liveness: 1 live, 0 stopped.",
                value=1.0 if health.live else 0.0,
            )
            yield GaugeMetricFamily(
                "trading_engine_analytics_service_ready",
                "Analytics service readiness: 1 ready, 0 not ready.",
                value=1.0 if health.ready else 0.0,
            )
            yield GaugeMetricFamily(
                "trading_engine_analytics_engine_connected",
                "Trading-engine connection state: 1 connected, 0 disconnected.",
                value=1.0 if health.engine_connected else 0.0,
            )
            yield CounterMetricFamily(
                "trading_engine_analytics_messages_received_total",
                "Total inbound messages received by the analytics service.",
                value=health.messages_received,
            )
            yield GaugeMetricFamily(
                "trading_engine_analytics_last_message_timestamp_seconds",
                "Timestamp of the most recently received inbound message.",
                value=health.last_message_timestamp or 0.0,
            )

        if self._persistence_health is not None:
            healthy = self._persistence_health()
            yield GaugeMetricFamily(
                "trading_engine_analytics_postgres_health",
                "PostgreSQL dependency health: 1 healthy, 0 unhealthy.",
                value=1.0 if healthy else 0.0,
            )

    @staticmethod
    def _error_family(snapshot):
        family = CounterMetricFamily(
            "trading_engine_analytics_errors_total",
            "Total service errors by category.",
            labels=["type"],
        )
        values = {
            "parse": snapshot.parse_error_count,
            "processing": snapshot.processing_error_count,
            "persistence": snapshot.persistence_error_count,
            "publish": snapshot.publish_error_count,
            "unknown": snapshot.unknown_error_count,
        }
        for error_type, value in values.items():
            family.add_metric([error_type], value)
        return family

    @staticmethod
    def _persistence_family(snapshot):
        family = CounterMetricFamily(
            "trading_engine_analytics_persistence_operations_total",
            "Total completed persistence operations by outcome.",
            labels=["outcome"],
        )
        family.add_metric(["success"], snapshot.success_count)
        family.add_metric(["failure"], snapshot.failure_count)
        return family

    def describe(self):
        return []


class PrometheusExporter:
    """Own a dedicated Prometheus registry and optional HTTP exposition server."""

    def __init__(
        self,
        *,
        service_metrics: ServiceMetrics,
        processing_latency_metrics: ProcessingLatencyMetrics,
        trade_throughput_metrics: TradeThroughputMetrics,
        risk_metrics: RiskMetrics,
        error_metrics: ErrorMetrics,
        persistence_metrics: PersistenceMetrics,
        health_metrics: ServiceHealthMetrics | None = None,
        persistence_health: Callable[[], bool | None] | None = None,
        registry: CollectorRegistry | None = None,
    ) -> None:
        self.registry = registry or CollectorRegistry()
        self._collector = AnalyticsPrometheusCollector(
            service_metrics=service_metrics,
            processing_latency_metrics=processing_latency_metrics,
            trade_throughput_metrics=trade_throughput_metrics,
            risk_metrics=risk_metrics,
            error_metrics=error_metrics,
            persistence_metrics=persistence_metrics,
            backpressure_metrics=backpressure_metrics,
            health_metrics=health_metrics,
            persistence_health=persistence_health,
        )
        self.registry.register(self._collector)
        self._server = None
        self._thread = None
        self._lock = Lock()

    @property
    def running(self) -> bool:
        """Return whether the HTTP exposition server is running."""
        with self._lock:
            return self._server is not None

    def start(self, *, port: int, host: str = "0.0.0.0") -> None:
        """Start the Prometheus HTTP exposition server."""
        if not isinstance(port, int):
            raise TypeError("port must be an integer")
        if not 0 <= port <= 65535:
            raise ValueError("port must be between 0 and 65535")

        with self._lock:
            if self._server is not None:
                raise RuntimeError("Prometheus exporter is already running")

            self._server, self._thread = start_http_server(
                port,
                addr=host,
                registry=self.registry,
            )

    def stop(self) -> None:
        """Stop the Prometheus HTTP exposition server."""
        with self._lock:
            server = self._server
            thread = self._thread
            self._server = None
            self._thread = None

        if server is None:
            return

        server.shutdown()
        server.server_close()
        if thread is not None:
            thread.join(timeout=2.0)
            if thread.is_alive():
                raise RuntimeError(
                    "Prometheus exporter server thread did not stop cleanly"
                )


__all__ = ["AnalyticsPrometheusCollector", "PrometheusExporter"]
