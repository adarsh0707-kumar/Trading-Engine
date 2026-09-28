from prometheus_client import CollectorRegistry, generate_latest

from analytics.observability import (
    ErrorMetrics,
    PersistenceMetrics,
    ProcessingLatencyMetrics,
    RiskMetrics,
    ServiceHealthMetrics,
    ServiceMetrics,
    TradeThroughputMetrics,
)
from analytics.observability.prometheus import AnalyticsPrometheusCollector


def test_prometheus_exposes_service_health():
    health = ServiceHealthMetrics()
    health.mark_started()
    health.mark_engine_connected()
    health.record_message(10.0)

    registry = CollectorRegistry()
    registry.register(
        AnalyticsPrometheusCollector(
            service_metrics=ServiceMetrics(),
            processing_latency_metrics=ProcessingLatencyMetrics(),
            trade_throughput_metrics=TradeThroughputMetrics(),
            risk_metrics=RiskMetrics(),
            error_metrics=ErrorMetrics(),
            persistence_metrics=PersistenceMetrics(),
            health_metrics=health,
        )
    )

    output = generate_latest(registry).decode()
    assert "trading_engine_analytics_service_live 1.0" in output
    assert "trading_engine_analytics_service_ready 1.0" in output
    assert "trading_engine_analytics_engine_connected 1.0" in output
    assert "trading_engine_analytics_messages_received_total 1.0" in output
