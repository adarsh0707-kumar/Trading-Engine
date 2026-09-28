"""Tests for Prometheus backpressure metrics."""

from analytics.observability import (
    BackpressureMetrics,
    ErrorMetrics,
    PersistenceMetrics,
    ProcessingLatencyMetrics,
    PrometheusExporter,
    RiskMetrics,
    ServiceHealthMetrics,
    ServiceMetrics,
    TradeThroughputMetrics,
)
from prometheus_client import CollectorRegistry


def test_prometheus_exposes_backpressure_counters() -> None:
    backpressure = BackpressureMetrics()
    backpressure.record_enqueued()
    backpressure.record_rejected()
    backpressure.set_queue_depth(3)

    registry = CollectorRegistry()
    exporter = PrometheusExporter(
        service_metrics=ServiceMetrics(),
        processing_latency_metrics=ProcessingLatencyMetrics(),
        trade_throughput_metrics=TradeThroughputMetrics(window_seconds=60),
        risk_metrics=RiskMetrics(),
        error_metrics=ErrorMetrics(),
        backpressure_metrics=backpressure,
        persistence_metrics=PersistenceMetrics(),
        health_metrics=ServiceHealthMetrics(),
        registry=registry,
    )

    samples = {
        sample.name: sample.value
        for metric in exporter.registry.collect()
        for sample in metric.samples
    }

    assert samples["trading_engine_analytics_backpressure_queue_depth"] == 3
    assert samples["trading_engine_analytics_backpressure_enqueued_total"] == 1
    assert samples["trading_engine_analytics_backpressure_rejected_total"] == 1
