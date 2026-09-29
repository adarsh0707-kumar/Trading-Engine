from __future__ import annotations

import socket
import struct
import threading
import time

import pytest

from analytics.ingestion.socket_client import (
    SocketClient,
    SocketProtocolError,
)


def test_frame_uses_big_endian_length() -> None:
    payload = '{"type":"TRADE"}'

    frame = SocketClient.frame(payload)

    assert frame[:4] == struct.pack(
        ">I",
        len(payload.encode("utf-8")),
    )

    assert frame[4:] == payload.encode("utf-8")


def test_extracts_fragmented_frame() -> None:
    client = SocketClient(
        "127.0.0.1",
        9000,
        reconnect=False,
    )

    payload = '{"type":"TRADE"}'
    frame = SocketClient.frame(payload)

    client._buffer.extend(frame[:2])

    assert client._extract_frames() == []

    client._buffer.extend(frame[2:])

    assert client._extract_frames() == [payload]


def test_extracts_multiple_frames_from_one_read() -> None:
    client = SocketClient(
        "127.0.0.1",
        9000,
        reconnect=False,
    )

    first = '{"type":"TRADE","request_id":"1"}'
    second = '{"type":"TRADE","request_id":"2"}'

    client._buffer.extend(
        SocketClient.frame(first)
        + SocketClient.frame(second)
    )

    assert client._extract_frames() == [
        first,
        second,
    ]


def test_incomplete_payload_remains_buffered() -> None:
    client = SocketClient(
        "127.0.0.1",
        9000,
        reconnect=False,
    )

    payload = '{"type":"TRADE"}'
    frame = SocketClient.frame(payload)

    client._buffer.extend(frame[:-1])

    assert client._extract_frames() == []
    assert bytes(client._buffer) == frame[:-1]


def test_rejects_oversized_payload() -> None:
    client = SocketClient(
        "127.0.0.1",
        9000,
        reconnect=False,
        max_payload_size=10,
    )

    client._buffer.extend(
        struct.pack(">I", 11)
    )

    with pytest.raises(SocketProtocolError):
        client._extract_frames()


def test_rejects_invalid_utf8() -> None:
    client = SocketClient(
        "127.0.0.1",
        9000,
        reconnect=False,
    )

    payload = b"\xff\xfe"

    client._buffer.extend(
        struct.pack(">I", len(payload))
        + payload
    )

    with pytest.raises(SocketProtocolError):
        client._extract_frames()


def test_heartbeat_is_handled_without_message_callback() -> None:
    received: list[str] = []

    client = SocketClient(
        "127.0.0.1",
        9000,
        reconnect=False,
        on_message=received.append,
    )

    heartbeat = (
        "{"
        '"type":"HEARTBEAT",'
        '"request_id":"heartbeat-1",'
        '"timestamp":"2026-09-10T00:00:00Z",'
        '"payload":"PING"'
        "}"
    )

    client._handle_payload(heartbeat)

    assert received == []


def test_send_requires_connection() -> None:
    client = SocketClient(
        "127.0.0.1",
        9000,
        reconnect=False,
    )

    with pytest.raises(ConnectionError):
        client.send('{"type":"TRADE"}')


def test_stop_is_idempotent() -> None:
    client = SocketClient(
        "127.0.0.1",
        9000,
        reconnect=False,
    )

    client.stop()
    client.stop()

    assert not client.is_running()


def test_socketpair_receive_fragmented_frame() -> None:
    server_socket, client_socket = socket.socketpair()

    messages: list[str] = []

    client = SocketClient(
        "127.0.0.1",
        9000,
        reconnect=False,
        on_message=messages.append,
    )

    # Replace the connection setup for this transport-level test.
    client._socket = client_socket
    client._connected = True
    client._running = True

    thread = threading.Thread(
        target=client._receive_loop,
        daemon=True,
    )
    thread.start()

    payload = '{"type":"TRADE","request_id":"fragmented"}'
    frame = SocketClient.frame(payload)

    server_socket.send(frame[:3])
    time.sleep(0.02)
    server_socket.send(frame[3:])

    deadline = time.monotonic() + 1.0

    while (
        not messages
        and time.monotonic() < deadline
    ):
        time.sleep(0.01)

    client._stop_event.set()
    server_socket.close()
    client_socket.close()
    thread.join(timeout=1.0)

    assert messages == [payload]


def test_message_callback_failure_does_not_stop_receive_loop() -> None:
    server_socket, client_socket = socket.socketpair()
    received: list[str] = []

    def on_message(payload: str) -> None:
        received.append(payload)
        if len(received) == 1:
            raise RuntimeError("simulated callback failure")

    client = SocketClient("127.0.0.1", 9000, reconnect=False, on_message=on_message)
    client._socket = client_socket
    client._connected = True
    client._running = True

    thread = threading.Thread(target=client._receive_loop, daemon=True)
    thread.start()

    first = '{"type":"TRADE","request_id":"first"}'
    second = '{"type":"TRADE","request_id":"second"}'
    server_socket.sendall(SocketClient.frame(first) + SocketClient.frame(second))

    deadline = time.monotonic() + 1.0
    while len(received) < 2 and time.monotonic() < deadline:
        time.sleep(0.01)

    client._stop_event.set()
    server_socket.close()
    client_socket.close()
    thread.join(timeout=1.0)

    assert received == [first, second]
    assert not thread.is_alive()


def test_disconnect_callback_failure_does_not_break_shutdown() -> None:
    def on_disconnect() -> None:
        raise RuntimeError("simulated disconnect callback failure")

    client = SocketClient(
        "127.0.0.1",
        9000,
        reconnect=False,
        on_disconnect=on_disconnect,
    )
    client._connected = True
    client._running = True

    client.stop()

    assert not client.is_running()
    assert not client.is_connected()


class _FakeSocket:
    def __init__(self, receives: list[bytes]) -> None:
        self._receives = iter(receives)
        self.closed = False

    def settimeout(self, timeout: float) -> None:
        del timeout

    def recv(self, size: int) -> bytes:
        del size
        try:
            return next(self._receives)
        except StopIteration:
            return b""

    def send(self, data: bytes) -> int:
        return len(data)

    def shutdown(self, how: int) -> None:
        del how
        if self.closed:
            raise OSError("socket already closed")

    def close(self) -> None:
        self.closed = True


def test_reconnects_after_unexpected_disconnect(monkeypatch) -> None:
    first_socket = _FakeSocket([b""])
    second_payload = '{"type":"TRADE","request_id":"recovered"}'
    second_socket = _FakeSocket([SocketClient.frame(second_payload)])

    sockets = iter([first_socket, second_socket])
    connect_calls: list[tuple[str, int]] = []
    messages: list[str] = []
    connected = threading.Event()

    def create_connection(address: tuple[str, int], timeout: float):
        del timeout
        connect_calls.append(address)
        try:
            return next(sockets)
        except StopIteration as exc:
            raise AssertionError("unexpected extra reconnect") from exc

    def on_message(payload: str) -> None:
        messages.append(payload)
        client.stop()

    client = SocketClient(
        "127.0.0.1",
        9000,
        reconnect=True,
        reconnect_delay=0.01,
        on_connect=connected.set,
        on_message=on_message,
    )

    monkeypatch.setattr(socket, "create_connection", create_connection)

    client.start()

    deadline = time.monotonic() + 2.0
    while not messages and time.monotonic() < deadline:
        time.sleep(0.01)

    client.stop()

    assert messages == [second_payload]
    assert connect_calls == [
        ("127.0.0.1", 9000),
        ("127.0.0.1", 9000),
    ]
    assert connected.is_set()
    assert not client.is_running()
    assert not client.is_connected()
    assert first_socket.closed
    assert second_socket.closed


def test_retries_connection_failure_before_connecting(monkeypatch) -> None:
    payload = '{"type":"TRADE","request_id":"after-connect-retry"}'
    recovered_socket = _FakeSocket([SocketClient.frame(payload)])

    attempts = 0
    messages: list[str] = []

    def create_connection(address: tuple[str, int], timeout: float):
        nonlocal attempts
        del address, timeout
        attempts += 1

        if attempts == 1:
            raise OSError("simulated connection refusal")

        return recovered_socket

    def on_message(received: str) -> None:
        messages.append(received)
        client.stop()

    client = SocketClient(
        "127.0.0.1",
        9000,
        reconnect=True,
        reconnect_delay=0.01,
        on_message=on_message,
    )

    monkeypatch.setattr(socket, "create_connection", create_connection)

    client.start()

    deadline = time.monotonic() + 2.0
    while not messages and time.monotonic() < deadline:
        time.sleep(0.01)

    client.stop()

    assert attempts == 2
    assert messages == [payload]
    assert not client.is_running()
    assert not client.is_connected()
    assert recovered_socket.closed
