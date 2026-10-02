"""Tests for the Gateway analytics TCP receiver."""

from __future__ import annotations

import json
import socket
import struct
import threading
import time

import pytest

from analytics.integration.gateway_receiver import (
    GatewayAnalyticsReceiver,
    GatewayReceiverProtocolError,
)


VALID_MESSAGE = json.dumps(
    {
        "version": 1,
        "type": "TRADE",
        "event_id": "trade-00000001-buy-1-sell-1",
        "request_id": "trade-00000001-buy-1-sell-1",
        "timestamp": "2026-10-02T12:00:01.000Z",
        "payload": json.dumps(
            {
                "trade_id": "trade-00000001-buy-1-sell-1",
                "symbol": "SIM",
                "price": 100.25,
                "quantity": 10,
                "taker_order_id": "buy-1",
                "maker_order_id": "sell-1",
                "taker_side": "BUY",
                "buy_order_id": "buy-1",
                "sell_order_id": "sell-1",
            }
        ),
    },
    separators=(",", ":"),
)


def _free_port() -> int:
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as probe:
        probe.bind(("127.0.0.1", 0))
        return int(probe.getsockname()[1])


def _frame(payload: str) -> bytes:
    encoded = payload.encode("utf-8")
    return struct.pack(">I", len(encoded)) + encoded


def _wait_until(predicate, timeout: float = 2.0) -> None:
    deadline = time.monotonic() + timeout
    while time.monotonic() < deadline:
        if predicate():
            return
        time.sleep(0.01)
    assert predicate()


def test_extracts_partial_and_multiple_frames() -> None:
    receiver = GatewayAnalyticsReceiver("127.0.0.1", 8000)

    first = _frame(VALID_MESSAGE)
    second = _frame(VALID_MESSAGE.replace("trade-00000001", "trade-00000002"))

    buffer = bytearray(first[:3])
    assert receiver._extract_frames(buffer) == []

    buffer.extend(first[3:] + second)
    assert receiver._extract_frames(buffer) == [VALID_MESSAGE, second[4:].decode()]
    assert buffer == bytearray()


def test_rejects_oversized_frame() -> None:
    receiver = GatewayAnalyticsReceiver(
        "127.0.0.1",
        8000,
        max_payload_size=16,
    )
    buffer = bytearray(struct.pack(">I", 17))

    with pytest.raises(
        GatewayReceiverProtocolError,
        match="exceeds maximum frame size",
    ):
        receiver._extract_frames(buffer)


def test_rejects_invalid_utf8() -> None:
    receiver = GatewayAnalyticsReceiver("127.0.0.1", 8000)
    payload = struct.pack(">I", 2) + b"\xff\xfe"
    buffer = bytearray(payload)

    with pytest.raises(
        GatewayReceiverProtocolError,
        match="valid UTF-8",
    ):
        receiver._extract_frames(buffer)


def test_receives_framed_gateway_message() -> None:
    port = _free_port()
    messages: list[str] = []
    connected = threading.Event()
    received = threading.Event()

    receiver = GatewayAnalyticsReceiver(
        "127.0.0.1",
        port,
        on_message=lambda message: (
            messages.append(message),
            received.set(),
        ),
        on_connect=connected.set,
    )

    receiver.start()

    try:
        _wait_until(lambda: receiver.is_running())

        with socket.create_connection(("127.0.0.1", port), timeout=2.0) as client:
            client.sendall(_frame(VALID_MESSAGE[:80]))
            client.sendall(_frame(VALID_MESSAGE[80:]))

            # The receiver should expose complete frames, not TCP chunks.
            _wait_until(received.is_set)
            _wait_until(lambda: len(messages) == 2)

        assert connected.is_set()
        assert messages == [VALID_MESSAGE[:80], VALID_MESSAGE[80:]]
    finally:
        receiver.stop()

    assert not receiver.is_running()
    assert not receiver.is_connected()


def test_receives_multiple_frames_in_one_tcp_write() -> None:
    port = _free_port()
    messages: list[str] = []
    received = threading.Event()

    second = VALID_MESSAGE.replace(
        "trade-00000001",
        "trade-00000002",
    )

    receiver = GatewayAnalyticsReceiver(
        "127.0.0.1",
        port,
        on_message=lambda message: (
            messages.append(message),
            received.set(),
        ),
    )
    receiver.start()

    try:
        _wait_until(lambda: receiver.is_running())

        with socket.create_connection(("127.0.0.1", port), timeout=2.0) as client:
            client.sendall(_frame(VALID_MESSAGE) + _frame(second))
            _wait_until(received.is_set)
            _wait_until(lambda: len(messages) == 2)

        assert messages == [VALID_MESSAGE, second]
    finally:
        receiver.stop()


def test_receiver_accepts_a_new_gateway_connection_after_disconnect() -> None:
    port = _free_port()
    messages: list[str] = []
    connected_count = 0
    disconnected_count = 0
    lock = threading.Lock()
    second_connection = threading.Event()

    def on_connect() -> None:
        nonlocal connected_count
        with lock:
            connected_count += 1
            if connected_count >= 2:
                second_connection.set()

    def on_disconnect() -> None:
        nonlocal disconnected_count
        with lock:
            disconnected_count += 1

    receiver = GatewayAnalyticsReceiver(
        "127.0.0.1",
        port,
        on_message=messages.append,
        on_connect=on_connect,
        on_disconnect=on_disconnect,
    )
    receiver.start()

    try:
        _wait_until(lambda: receiver.is_running())

        with socket.create_connection(("127.0.0.1", port), timeout=2.0) as first:
            first.sendall(_frame(VALID_MESSAGE))

        _wait_until(lambda: disconnected_count == 1)

        with socket.create_connection(("127.0.0.1", port), timeout=2.0) as second:
            second.sendall(
                _frame(
                    VALID_MESSAGE.replace(
                        "trade-00000001",
                        "trade-00000002",
                    )
                )
            )

        _wait_until(second_connection.is_set)
        _wait_until(lambda: len(messages) == 2)

        assert connected_count == 2
        assert disconnected_count == 2
    finally:
        receiver.stop()
