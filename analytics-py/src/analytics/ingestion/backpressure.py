"""Bounded message queue for analytics backpressure control."""

from __future__ import annotations

from dataclasses import dataclass
from queue import Empty, Full, Queue
from threading import Event, Lock, Thread, current_thread
from typing import Callable


@dataclass(frozen=True, slots=True)
class BackpressureSnapshot:
    """Immutable backpressure state."""

    capacity: int
    queue_depth: int
    enqueued_count: int
    rejected_count: int


class BackpressureQueue:
    """Bounded FIFO queue with explicit rejection metrics."""

    def __init__(self, *, capacity: int) -> None:
        if isinstance(capacity, bool) or not isinstance(capacity, int):
            raise ValueError("capacity must be an integer greater than 0")
        if capacity <= 0:
            raise ValueError("capacity must be greater than 0")

        self.capacity = capacity
        self._queue: Queue[str] = Queue(maxsize=capacity)
        self._lock = Lock()
        self._enqueued_count = 0
        self._rejected_count = 0

    def put(self, message: str, *, timeout: float) -> bool:
        """Enqueue a message, rejecting it when the bounded queue is full."""
        if timeout < 0:
            raise ValueError("timeout must not be negative")

        try:
            self._queue.put(message, timeout=timeout)
        except Full:
            with self._lock:
                self._rejected_count += 1
            return False

        with self._lock:
            self._enqueued_count += 1
        return True

    def get(self, *, timeout: float) -> str | None:
        """Return the next message, or None when the queue is empty."""
        try:
            return self._queue.get(timeout=timeout)
        except Exception as exc:
            from queue import Empty

            if isinstance(exc, Empty):
                return None
            raise

    def task_done(self) -> None:
        """Mark one dequeued message as processed."""
        self._queue.task_done()

    def join(self) -> None:
        """Wait until all currently queued messages are processed."""
        self._queue.join()

    def snapshot(self) -> BackpressureSnapshot:
        """Return the current queue depth and counters."""
        with self._lock:
            return BackpressureSnapshot(
                capacity=self.capacity,
                queue_depth=self._queue.qsize(),
                enqueued_count=self._enqueued_count,
                rejected_count=self._rejected_count,
            )


class BackpressureWorker:
    """Process queued messages on a dedicated worker thread."""

    def __init__(
        self,
        queue: BackpressureQueue,
        handler: Callable[[str], None],
    ) -> None:
        self.queue = queue
        self.handler = handler
        self._stop_event = Event()
        self._thread: Thread | None = None

    @property
    def running(self) -> bool:
        return self._thread is not None and self._thread.is_alive()

    def start(self) -> None:
        """Start the queue worker once."""
        if self.running:
            return

        self._stop_event.clear()
        self._thread = Thread(
            target=self._run,
            name="analytics-backpressure-worker",
            daemon=True,
        )
        self._thread.start()

    def stop(self, *, drain: bool = True) -> None:
        """Stop the worker, optionally draining queued messages first."""
        if drain:
            self.queue.join()

        self._stop_event.set()
        thread = self._thread
        if thread is not None and thread is not current_thread():
            thread.join(timeout=2.0)
        self._thread = None

    def _run(self) -> None:
        while not self._stop_event.is_set() or self.queue.snapshot().queue_depth:
            message = self.queue.get(timeout=0.05)
            if message is None:
                continue
            try:
                self.handler(message)
            finally:
                self.queue.task_done()
