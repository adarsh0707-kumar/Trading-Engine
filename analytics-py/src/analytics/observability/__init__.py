"""Observability primitives for the analytics service."""

from analytics.observability.health import check_postgres_health
from analytics.observability.backpressure import (
    BackpressureMetrics,
    BackpressureMetricsSnapshot,
)
from analytics.observability.health_metrics import (
    ServiceHealthMetrics,
    ServiceHealthSnapshot,
)
from analytics.observability.logging_config import (
    DEFAULT_LOG_FORMAT,
    DEFAULT_LOG_LEVEL,
    LoggingConfigurationError,
    configure_logging,
    get_configured_log_level,
)
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
    "BackpressureMetrics",
    "BackpressureMetricsSnapshot",
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
    "ServiceHealthMetrics",
    "ServiceHealthSnapshot",
    "TradeThroughputMetrics",
    "TradeThroughputSnapshot",
    "check_postgres_health",
    "DEFAULT_LOG_FORMAT",
    "DEFAULT_LOG_LEVEL",
    "LoggingConfigurationError",
    "configure_logging",
    "get_configured_log_level",
]
