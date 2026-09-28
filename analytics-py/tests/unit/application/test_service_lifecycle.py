"""Tests for graceful AnalyticsService lifecycle behavior."""

from unittest.mock import Mock

import pytest

from analytics.config.settings import Settings
from analytics.main import AnalyticsService


def _service() -> AnalyticsService:
    service = AnalyticsService(
        Settings(),
        publish_sink=Mock(),
    )
    service.client = Mock()
    return service


def test_start_is_idempotent() -> None:
    service = _service()

    service.start()
    service.start()

    service.client.start.assert_called_once()
    assert service.health_metrics.snapshot().live is True


def test_stop_is_idempotent() -> None:
    service = _service()

    service.start()
    service.stop()
    service.stop()

    service.client.stop.assert_called_once()
    snapshot = service.health_metrics.snapshot()
    assert snapshot.live is False
    assert snapshot.ready is False


def test_stop_before_start_is_safe() -> None:
    service = _service()

    service.stop()

    service.client.stop.assert_called_once()
    snapshot = service.health_metrics.snapshot()
    assert snapshot.live is False
    assert snapshot.ready is False


def test_failed_start_rolls_back_lifecycle_state() -> None:
    service = _service()
    error = RuntimeError("socket startup failed")
    service.client.start.side_effect = error

    with pytest.raises(RuntimeError, match="socket startup failed"):
        service.start()

    assert service.client.start.call_count == 1
    assert service.health_metrics.snapshot().live is False

    service.client.start.side_effect = None
    service.start()

    assert service.client.start.call_count == 2
    assert service.health_metrics.snapshot().live is True


def test_stop_cleans_owned_repositories_when_client_stop_fails() -> None:
    service = _service()
    repositories = Mock()
    service.repositories = repositories
    service._owns_repositories = True
    service.client.stop.side_effect = RuntimeError("socket shutdown failed")

    with pytest.raises(RuntimeError, match="socket shutdown failed"):
        service.stop()

    repositories.close.assert_called_once()
    assert service._owns_repositories is False
    assert service.health_metrics.snapshot().live is False


def test_stop_cleans_metrics_when_client_stop_fails() -> None:
    service = _service()
    exporter = Mock()
    exporter.running = True
    service.prometheus_exporter = exporter
    service.client.stop.side_effect = RuntimeError("socket shutdown failed")

    with pytest.raises(RuntimeError, match="socket shutdown failed"):
        service.stop()

    exporter.stop.assert_called_once()
    assert service.health_metrics.snapshot().live is False


def test_stop_preserves_first_cleanup_error_but_finishes_cleanup() -> None:
    service = _service()
    repositories = Mock()
    service.repositories = repositories
    service._owns_repositories = True
    service.client.stop.side_effect = RuntimeError("client failed")
    repositories.close.side_effect = RuntimeError("repository failed")

    with pytest.raises(RuntimeError, match="client failed"):
        service.stop()

    repositories.close.assert_called_once()
    assert service.health_metrics.snapshot().live is False
