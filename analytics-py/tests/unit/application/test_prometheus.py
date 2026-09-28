from analytics.config import Settings
from analytics.main import AnalyticsService


class FakeExporter:
    def __init__(self):
        self.running = False
        self.started = None
        self.stop_count = 0

    def start(self, *, port: int, host: str) -> None:
        self.started = (port, host)
        self.running = True

    def stop(self) -> None:
        self.stop_count += 1
        self.running = False


def test_service_starts_configured_prometheus_exporter():
    exporter = FakeExporter()
    service = AnalyticsService(
        Settings(metrics_host="127.0.0.1", metrics_port=9101),
        prometheus_exporter=exporter,
    )

    service.start_metrics_server()

    assert exporter.started == (9101, "127.0.0.1")
    assert exporter.running is True


def test_service_does_not_start_disabled_prometheus_exporter():
    exporter = FakeExporter()
    service = AnalyticsService(
        Settings(metrics_port=None),
        prometheus_exporter=exporter,
    )

    service.start_metrics_server()

    assert exporter.started is None
    assert exporter.running is False


def test_service_stops_running_prometheus_exporter():
    exporter = FakeExporter()
    service = AnalyticsService(
        Settings(metrics_port=9101),
        prometheus_exporter=exporter,
    )

    service.start_metrics_server()
    service.stop_metrics_server()

    assert exporter.stop_count == 1
    assert exporter.running is False
