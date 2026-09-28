from analytics.observability.health_metrics import ServiceHealthMetrics


def test_initial_health_is_stopped():
    snapshot = ServiceHealthMetrics().snapshot()
    assert snapshot.live is False
    assert snapshot.ready is False
    assert snapshot.engine_connected is False
    assert snapshot.messages_received == 0
    assert snapshot.last_message_timestamp is None


def test_health_lifecycle_and_messages():
    metrics = ServiceHealthMetrics()
    metrics.mark_started()
    metrics.mark_engine_connected()
    metrics.record_message(12.5)
    snapshot = metrics.snapshot()
    assert snapshot.live is True
    assert snapshot.ready is True
    assert snapshot.engine_connected is True
    assert snapshot.messages_received == 1
    assert snapshot.last_message_timestamp == 12.5


def test_disconnect_and_stop_clear_availability():
    metrics = ServiceHealthMetrics()
    metrics.mark_started()
    metrics.mark_engine_connected()
    metrics.mark_engine_disconnected()
    assert metrics.snapshot().ready is False
    metrics.mark_stopped()
    snapshot = metrics.snapshot()
    assert snapshot.live is False
    assert snapshot.engine_connected is False


def test_message_timestamp_must_be_numeric():
    metrics = ServiceHealthMetrics()
    try:
        metrics.record_message("invalid")
    except TypeError:
        pass
    else:
        raise AssertionError("expected TypeError")


def test_reset_returns_initial_state():
    metrics = ServiceHealthMetrics()
    metrics.mark_started()
    metrics.mark_engine_connected()
    metrics.record_message(4.0)
    metrics.reset()
    snapshot = metrics.snapshot()
    assert snapshot.live is False
    assert snapshot.ready is False
    assert snapshot.messages_received == 0
