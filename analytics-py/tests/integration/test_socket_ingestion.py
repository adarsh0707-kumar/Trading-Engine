"""Deterministic integration tests for the socket ingestion transport."""

from __future__ import annotations

import json
import socket
import struct
import threading
import time

from analytics.ingestion import SocketClient


def _frame(payload: str) -> bytes:
    """Build a trading-engine-compatible protocol frame."""
    encoded = payload.encode("utf-8")
    return struct.pack(">I", len(encoded)) + encoded


def _start_deterministic_server(
    messages: list[str],
    *,
    fragment_size: int = 3,
) -> tuple[int, threading.Thread]:
    """Start a deterministic local TCP server.

    The server deliberately sends protocol frames in small fragments so
    the test exercises the same fragmented-TCP condition that the real
    engine can produce.
    """
    ready = threading.Event()
    server_port: list[int] = []
    server_error: list[BaseException] = []

    def server() -> None:
        try:
            with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as server_socket:
                server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
                server_socket.bind(("127.0.0.1", 0))
                server_socket.listen(1)

                server_port.append(server_socket.getsockname()[1])
                ready.set()

                connection, _ = server_socket.accept()

                with connection:
                    for message in messages:
                        frame = _frame(message)

                        for offset in range(0, len(frame), fragment_size):
                            connection.sendall(
                                frame[offset : offset + fragment_size]
                            )
                            time.sleep(0.001)

        except BaseException as exc:
            server_error.append(exc)
            ready.set()

    thread = threading.Thread(
        target=server,
        name="deterministic-socket-server",
        daemon=True,
    )
    thread.start()

    assert ready.wait(timeout=2.0), "deterministic server did not start"
    assert not server_error, server_error

    return server_port[0], thread


def test_socket_client_receives_cxx_compatible_messages() -> None:
    """Verify Python ingestion against the trading-engine wire protocol."""

    hello = json.dumps(
        {
            "type": "HELLO",
            "request_id": "",
            "timestamp": "",
            "payload": "Trading Engine transport connected",
        },
        separators=(",", ":"),
    )

    trade = json.dumps(
        {
            "type": "TRADE",
            "request_id": "trade-SIM-00000001-SIM-00000002",
            "timestamp": "2026-09-10T00:00:00Z",
            "payload": json.dumps(
                {
                    "symbol": "SIM",
                    "price": 98.57,
                    "quantity": 3,
                    "taker_order_id": "SIM-00000001",
                    "maker_order_id": "SIM-00000002",
                },
                separators=(",", ":"),
            ),
        },
        separators=(",", ":"),
    )

    port, server_thread = _start_deterministic_server(
        [hello, trade],
        fragment_size=3,
    )

    received: list[str] = []
    connected = threading.Event()
    disconnected = threading.Event()

    client = SocketClient(
        host="127.0.0.1",
        port=port,
        connect_timeout=2.0,
        receive_timeout=0.1,
        reconnect=False,
        on_connect=connected.set,
        on_disconnect=disconnected.set,
        on_message=received.append,
    )

    client.start()

    try:
        assert connected.wait(timeout=2.0), "client did not connect"

        deadline = time.monotonic() + 2.0

        while len(received) < 2 and time.monotonic() < deadline:
            time.sleep(0.01)

        assert received == [hello, trade]

        hello_message = json.loads(received[0])
        trade_message = json.loads(received[1])

        assert hello_message["type"] == "HELLO"
        assert hello_message["payload"] == (
            "Trading Engine transport connected"
        )

        assert trade_message["type"] == "TRADE"
        assert trade_message["request_id"] == (
            "trade-SIM-00000001-SIM-00000002"
        )

        trade_payload = json.loads(trade_message["payload"])

        assert trade_payload == {
            "symbol": "SIM",
            "price": 98.57,
            "quantity": 3,
            "taker_order_id": "SIM-00000001",
            "maker_order_id": "SIM-00000002",
        }

    finally:
        client.stop()

    server_thread.join(timeout=2.0)

    assert disconnected.is_set()
    assert not client.is_running()
    assert not client.is_connected()
    assert not server_thread.is_alive()
