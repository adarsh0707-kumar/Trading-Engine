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
