from analytics.config import Settings
from analytics.main import AnalyticsService
from analytics.observability import ServiceHealthMetrics


class FakeClient:
    def __init__(self):
        self.started = False
        self.stopped = False

    def start(self):
        self.started = True

    def stop(self):
        self.stopped = True


def test_service_start_marks_live():
    health = ServiceHealthMetrics()
    service = AnalyticsService(Settings(), health_metrics=health)
    service.client = FakeClient()
    service.start()
    snapshot = health.snapshot()
    assert snapshot.live is True
    assert snapshot.ready is False


def test_connect_and_disconnect_update_health():
    health = ServiceHealthMetrics()
    service = AnalyticsService(Settings(), health_metrics=health)
    service.health_metrics.mark_started()
    service._handle_connect()
    assert health.snapshot().ready is True
    assert health.snapshot().engine_connected is True
    service._handle_disconnect()
    assert health.snapshot().ready is False


def test_stop_marks_health_unavailable():
    health = ServiceHealthMetrics()
    service = AnalyticsService(Settings(), health_metrics=health)
    service.client = FakeClient()
    health.mark_started()
    health.mark_engine_connected()
    service.stop()
    snapshot = health.snapshot()
    assert snapshot.live is False
    assert snapshot.ready is False
    assert snapshot.engine_connected is False
