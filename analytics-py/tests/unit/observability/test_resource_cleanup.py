"""Tests for deterministic resource cleanup."""

from unittest.mock import Mock

import pytest

from analytics.ingestion.socket_client import SocketClient
from analytics.observability import (
    ErrorMetrics,
    PersistenceMetrics,
    ProcessingLatencyMetrics,
    PrometheusExporter,
    RiskMetrics,
    ServiceMetrics,
    TradeThroughputMetrics,
)
from prometheus_client import CollectorRegistry


def _exporter() -> PrometheusExporter:
    return PrometheusExporter(
        service_metrics=ServiceMetrics(),
        processing_latency_metrics=ProcessingLatencyMetrics(),
        trade_throughput_metrics=TradeThroughputMetrics(window_seconds=60),
        risk_metrics=RiskMetrics(),
        error_metrics=ErrorMetrics(),
        persistence_metrics=PersistenceMetrics(),
        registry=CollectorRegistry(),
    )


def test_socket_client_stop_clears_buffer_and_marks_disconnected() -> None:
    disconnected = Mock()
    client = SocketClient("127.0.0.1", 9000, on_disconnect=disconnected)

    client._socket = Mock()
    client._connected = True
    client._buffer.extend(b"stale-frame-data")

    client.stop()

    assert client._socket is None
    assert client._connected is False
    assert client._buffer == bytearray()
    disconnected.assert_called_once()


def test_prometheus_exporter_stop_closes_server() -> None:
    exporter = _exporter()
    server = Mock()
    thread = Mock()
    thread.is_alive.return_value = False

    exporter._server = server
    exporter._thread = thread

    exporter.stop()

    server.shutdown.assert_called_once()
    server.server_close.assert_called_once()
    thread.join.assert_called_once_with(timeout=2.0)
    assert exporter.running is False


def test_prometheus_exporter_reports_stuck_server_thread() -> None:
    exporter = _exporter()
    server = Mock()
    thread = Mock()
    thread.is_alive.return_value = True

    exporter._server = server
    exporter._thread = thread

    with pytest.raises(
        RuntimeError,
        match="server thread did not stop cleanly",
    ):
        exporter.stop()

    server.shutdown.assert_called_once()
    server.server_close.assert_called_once()
    thread.join.assert_called_once_with(timeout=2.0)
    assert exporter.running is False
