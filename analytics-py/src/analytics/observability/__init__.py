"""Observability primitives for the analytics service."""

from analytics.observability.health import check_postgres_health
from analytics.observability.metrics import (
    ErrorMetrics,
    ErrorMetricsSnapshot,
    PersistenceMetrics,
    PersistenceMetricsSnapshot,
    ProcessingLatencyMetrics,
    ProcessingLatencySnapshot,
    RiskMetrics,
    RiskMetricsSnapshot,
    ServiceMetrics,
    ServiceMetricsSnapshot,
    TradeThroughputMetrics,
    TradeThroughputSnapshot,
)
from analytics.observability.prometheus import (
    AnalyticsPrometheusCollector,
    PrometheusExporter,
)

__all__ = [
    "AnalyticsPrometheusCollector",
    "ErrorMetrics",
    "ErrorMetricsSnapshot",
    "PersistenceMetrics",
    "PersistenceMetricsSnapshot",
    "ProcessingLatencyMetrics",
    "ProcessingLatencySnapshot",
    "PrometheusExporter",
    "RiskMetrics",
    "RiskMetricsSnapshot",
    "ServiceMetrics",
    "ServiceMetricsSnapshot",
    "TradeThroughputMetrics",
    "TradeThroughputSnapshot",
    "check_postgres_health",
]
