from decimal import Decimal

from prometheus_client import CollectorRegistry, generate_latest

from analytics.observability import (
    ErrorMetrics,
    PersistenceMetrics,
    ProcessingLatencyMetrics,
    PrometheusExporter,
    RiskMetrics,
    ServiceMetrics,
    TradeThroughputMetrics,
)


def _exporter():
    return PrometheusExporter(
        service_metrics=ServiceMetrics(),
        processing_latency_metrics=ProcessingLatencyMetrics(),
        trade_throughput_metrics=TradeThroughputMetrics(window_seconds=60),
        risk_metrics=RiskMetrics(),
        error_metrics=ErrorMetrics(),
        persistence_metrics=PersistenceMetrics(),
        registry=CollectorRegistry(),
    )


def test_registry_exposes_service_and_latency_metrics():
    exporter = _exporter()

    exporter._collector._service_metrics.record_trade_success(0.25)
    exporter._collector._processing_latency_metrics.record(0.25)

    output = generate_latest(exporter.registry).decode()

    assert "trading_engine_analytics_processed_trades_total 1.0" in output
    assert "trading_engine_analytics_processing_latency_seconds_count 1.0" in output
    assert "trading_engine_analytics_processing_latency_seconds_sum 0.25" in output


def test_registry_exposes_throughput_risk_errors_and_persistence_metrics():
    exporter = _exporter()
    collector = exporter._collector

    collector._trade_throughput_metrics.record_trade(timestamp_seconds=100.0)
    collector._risk_metrics.record_snapshot(
        position=-4,
        realized_pnl=Decimal("12.50"),
        unrealized_pnl=Decimal("-2.25"),
        equity=Decimal("1010.25"),
        peak_equity=Decimal("1020.00"),
        drawdown=Decimal("9.75"),
    )
    collector._risk_metrics.record_warning_event()
    collector._risk_metrics.record_breached_event()
    collector._error_metrics.record_publish_error()
    collector._persistence_metrics.record_success(0.1)
    collector._persistence_metrics.record_failure(0.2)

    output = generate_latest(exporter.registry).decode()

    assert "trading_engine_analytics_trades_total 1.0" in output
    assert 'trading_engine_analytics_errors_total{type="publish"} 1.0' in output
    assert 'trading_engine_analytics_persistence_operations_total{outcome="success"} 1.0' in output
    assert 'trading_engine_analytics_persistence_operations_total{outcome="failure"} 1.0' in output
    assert "trading_engine_analytics_position -4.0" in output
    assert "trading_engine_analytics_realized_pnl 12.5" in output
    assert "trading_engine_analytics_unrealized_pnl -2.25" in output
    assert "trading_engine_analytics_risk_warnings_total 1.0" in output
    assert "trading_engine_analytics_risk_breaches_total 1.0" in output


def test_empty_latency_percentiles_are_exported_as_zero():
    exporter = _exporter()

    output = generate_latest(exporter.registry).decode()

    assert "trading_engine_analytics_processing_latency_p50_seconds 0.0" in output
    assert "trading_engine_analytics_processing_latency_p95_seconds 0.0" in output
    assert "trading_engine_analytics_processing_latency_p99_seconds 0.0" in output


def test_exporter_start_and_stop_lifecycle():
    exporter = _exporter()

    exporter.start(port=0)
    assert exporter.running is True

    exporter.stop()
    assert exporter.running is False

    exporter.stop()
