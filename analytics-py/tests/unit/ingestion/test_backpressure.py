"""Tests for bounded analytics backpressure."""

import time

from analytics.ingestion.backpressure import BackpressureQueue, BackpressureWorker


def test_queue_rejects_when_full() -> None:
    queue = BackpressureQueue(capacity=1)

    assert queue.put("first", timeout=0)
    assert not queue.put("second", timeout=0)

    snapshot = queue.snapshot()
    assert snapshot.queue_depth == 1
    assert snapshot.enqueued_count == 1
    assert snapshot.rejected_count == 1


def test_worker_drains_queue_before_shutdown() -> None:
    queue = BackpressureQueue(capacity=2)
    processed: list[str] = []
    worker = BackpressureWorker(queue, processed.append)

    worker.start()
    assert queue.put("one", timeout=0)
    assert queue.put("two", timeout=0)

    worker.stop(drain=True)

    assert processed == ["one", "two"]
    assert not worker.running
    assert queue.snapshot().queue_depth == 0


def test_worker_survives_handler_failure() -> None:
    queue = BackpressureQueue(capacity=2)
    processed: list[str] = []

    def handler(message: str) -> None:
        if message == "bad":
            raise RuntimeError("boom")
        processed.append(message)

    worker = BackpressureWorker(queue, handler)
    worker.start()
    assert queue.put("bad", timeout=0)
    assert queue.put("good", timeout=0)

    deadline = time.monotonic() + 2.0
    while not processed and time.monotonic() < deadline:
        time.sleep(0.01)

    worker.stop(drain=True)

    assert processed == ["good"]
