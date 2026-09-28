"""Observability primitives for the analytics service."""

from analytics.observability.health import check_postgres_health
from analytics.observability.metrics import (
    ErrorMetrics,
    ErrorMetricsSnapshot,
    PersistenceMetrics,
    PersistenceMetricsSnapshot,
    ProcessingLatencyMetrics,
    ProcessingLatencySnapshot,
    ServiceMetrics,
    ServiceMetricsSnapshot,
    TradeThroughputMetrics,
    TradeThroughputSnapshot,
    RiskMetrics,
    RiskMetricsSnapshot,
)

__all__ = [
    "ErrorMetrics",
    "ErrorMetricsSnapshot",
    "PersistenceMetrics",
    "PersistenceMetricsSnapshot",
    "ProcessingLatencyMetrics",
    "ProcessingLatencySnapshot",
    "ServiceMetrics",
    "ServiceMetricsSnapshot",
    "TradeThroughputMetrics",
    "TradeThroughputSnapshot",
    "RiskMetrics",
    "RiskMetricsSnapshot",
    "check_postgres_health",
]
