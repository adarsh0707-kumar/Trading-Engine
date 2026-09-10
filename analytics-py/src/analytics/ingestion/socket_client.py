"""TCP socket client for ingesting framed messages from the trading engine.

The trading engine uses the following wire protocol:

    4-byte unsigned payload length (big-endian)
    followed by
    UTF-8 JSON payload

This module is intentionally responsible only for transport-level concerns.
JSON/business-message parsing belongs to ``message_parser.py``.
"""

from __future__ import annotations

import logging
import socket
import struct
import threading
from collections.abc import Callable
from typing import Optional


logger = logging.getLogger(__name__)


class SocketProtocolError(Exception):
    """Raised when an invalid wire-protocol frame is received."""


class SocketClient:
    """TCP client for the trading engine's framed message protocol.

    Parameters
    ----------
    host:
        Trading engine host.
    port:
        Trading engine TCP port.
    connect_timeout:
        Timeout used while establishing a connection.
    receive_timeout:
        Socket receive timeout.
    reconnect:
        Whether to automatically reconnect after disconnection.
    reconnect_delay:
        Delay between reconnect attempts.
    max_payload_size:
        Maximum accepted payload size in bytes.
    on_message:
        Callback receiving each complete raw JSON payload.
    on_connect:
        Callback invoked after a successful connection.
    on_disconnect:
        Callback invoked after disconnection.
    """

    HEADER_SIZE = 4
    MAX_PAYLOAD_SIZE = 1024 * 1024

    def __init__(
        self,
        host: str,
        port: int,
        *,
        connect_timeout: float = 5.0,
        receive_timeout: float = 1.0,
        reconnect: bool = True,
        reconnect_delay: float = 1.0,
        max_payload_size: int = MAX_PAYLOAD_SIZE,
        on_message: Optional[Callable[[str], None]] = None,
        on_connect: Optional[Callable[[], None]] = None,
        on_disconnect: Optional[Callable[[], None]] = None,
    ) -> None:
        if not host:
            raise ValueError("host must not be empty")

        if not 1 <= port <= 65535:
            raise ValueError("port must be between 1 and 65535")

        if connect_timeout <= 0:
            raise ValueError("connect_timeout must be positive")

        if receive_timeout <= 0:
            raise ValueError("receive_timeout must be positive")

        if reconnect_delay < 0:
            raise ValueError("reconnect_delay must not be negative")

        if max_payload_size <= 0:
            raise ValueError("max_payload_size must be positive")

        self.host = host
        self.port = port
        self.connect_timeout = connect_timeout
        self.receive_timeout = receive_timeout
        self.reconnect = reconnect
        self.reconnect_delay = reconnect_delay
        self.max_payload_size = max_payload_size

        self.on_message = on_message
        self.on_connect = on_connect
        self.on_disconnect = on_disconnect

        self._socket: Optional[socket.socket] = None
        self._buffer = bytearray()

        self._running = False
        self._connected = False

        self._thread: Optional[threading.Thread] = None

        self._state_lock = threading.Lock()
        self._send_lock = threading.Lock()

        self._stop_event = threading.Event()

    @staticmethod
    def frame(payload: str) -> bytes:
        """Frame a UTF-8 payload using the trading-engine protocol."""

        encoded = payload.encode("utf-8")

        if len(encoded) > SocketClient.MAX_PAYLOAD_SIZE:
            raise SocketProtocolError(
                "payload exceeds maximum frame size"
            )

        return struct.pack(">I", len(encoded)) + encoded

    def start(self) -> None:
        """Start the background socket-ingestion thread."""

        with self._state_lock:
            if self._running:
                return

            self._running = True

        self._stop_event.clear()

        self._thread = threading.Thread(
            target=self._run,
            name="trading-engine-socket-client",
            daemon=True,
        )

        self._thread.start()

    def stop(self) -> None:
        """Stop the client and close the active socket."""

        with self._state_lock:
            self._running = False

        self._stop_event.set()
        self._close_socket()

        thread = self._thread

        if (
            thread is not None
            and thread is not threading.current_thread()
        ):
            thread.join(timeout=max(self.receive_timeout + 1.0, 2.0))

        self._thread = None

    def is_running(self) -> bool:
        """Return whether the client ingestion loop is running."""

        with self._state_lock:
            return self._running

    def is_connected(self) -> bool:
        """Return whether a TCP connection is currently established."""

        with self._state_lock:
            return self._connected

    def send(self, payload: str) -> None:
        """Send one raw JSON payload using the trading-engine frame format."""

        encoded = payload.encode("utf-8")

        if len(encoded) > self.max_payload_size:
            raise SocketProtocolError(
                "payload exceeds maximum frame size"
            )

        frame = struct.pack(">I", len(encoded)) + encoded

        with self._send_lock:
            current_socket = self._socket

            if current_socket is None:
                raise ConnectionError("socket is not connected")

            self._send_all(current_socket, frame)

    def _run(self) -> None:
        """Main background connection/reconnection loop."""

        while not self._stop_event.is_set():
            try:
                self._connect()
                self._receive_loop()

            except OSError as exc:
                if not self._stop_event.is_set():
                    logger.warning(
                        "Socket connection error: %s",
                        exc,
                    )

            except SocketProtocolError as exc:
                logger.error(
                    "Socket protocol error: %s",
                    exc,
                )

            finally:
                self._mark_disconnected()
                self._close_socket()

            if (
                not self.reconnect
                or self._stop_event.is_set()
            ):
                break

            self._stop_event.wait(self.reconnect_delay)

    def _connect(self) -> None:
        """Establish a TCP connection to the trading engine."""

        logger.info(
            "Connecting to trading engine at %s:%d",
            self.host,
            self.port,
        )

        connected_socket = socket.create_connection(
            (self.host, self.port),
            timeout=self.connect_timeout,
        )

        connected_socket.settimeout(
            self.receive_timeout
        )

        with self._state_lock:
            if not self._running:
                connected_socket.close()
                raise OSError("socket client is stopping")

            self._socket = connected_socket
            self._connected = True

        self._buffer.clear()

        logger.info(
            "Connected to trading engine at %s:%d",
            self.host,
            self.port,
        )

        if self.on_connect is not None:
            self.on_connect()

    def _receive_loop(self) -> None:
        """Receive TCP data and extract complete protocol frames."""

        while not self._stop_event.is_set():
            current_socket = self._socket

            if current_socket is None:
                return

            try:
                chunk = current_socket.recv(8192)

            except socket.timeout:
                continue

            if not chunk:
                return

            self._buffer.extend(chunk)

            for payload in self._extract_frames():
                self._handle_payload(payload)

    def _extract_frames(self) -> list[str]:
        """Extract all complete frames currently available in the buffer."""

        payloads: list[str] = []

        while True:
            if len(self._buffer) < self.HEADER_SIZE:
                break

            payload_size = struct.unpack(
                ">I",
                self._buffer[: self.HEADER_SIZE],
            )[0]

            if payload_size > self.max_payload_size:
                raise SocketProtocolError(
                    "received payload exceeds maximum frame size"
                )

            total_size = self.HEADER_SIZE + payload_size

            if len(self._buffer) < total_size:
                break

            payload_bytes = bytes(
                self._buffer[
                    self.HEADER_SIZE : total_size
                ]
            )

            del self._buffer[:total_size]

            try:
                payload = payload_bytes.decode("utf-8")
            except UnicodeDecodeError as exc:
                raise SocketProtocolError(
                    "received payload is not valid UTF-8"
                ) from exc

            payloads.append(payload)

        return payloads

    def _handle_payload(self, payload: str) -> None:
        """Handle one complete raw payload.

        Heartbeat messages are handled at the transport layer so that
        the C++ server can verify client liveness.

        All other messages are forwarded unchanged to ``on_message``.
        """

        if self._is_heartbeat(payload):
            self._handle_heartbeat(payload)
            return

        if self.on_message is not None:
            self.on_message(payload)

    @staticmethod
    def _is_heartbeat(payload: str) -> bool:
        """Return whether a payload is a heartbeat message.

        The check is deliberately lightweight. Full JSON validation belongs
        to Phase 3.5.
        """

        return (
            '"type":"HEARTBEAT"' in payload
            and '"payload":"PING"' in payload
        )

    def _handle_heartbeat(self, payload: str) -> None:
        """Respond to a trading-engine heartbeat."""

        request_id = self._extract_json_string(
            payload,
            "request_id",
        )

        timestamp = self._extract_json_string(
            payload,
            "timestamp",
        )

        response = (
            "{"
            '"type":"HEARTBEAT",'
            f'"request_id":"{self._escape_json_string(request_id)}",'
            f'"timestamp":"{self._escape_json_string(timestamp)}",'
            '"payload":"OK"'
            "}"
        )

        try:
            self.send(response)
        except ConnectionError:
            logger.debug(
                "Heartbeat response could not be sent because "
                "the socket disconnected."
            )

    @staticmethod
    def _extract_json_string(
        payload: str,
        key: str,
    ) -> str:
        """Extract a simple JSON string field.

        This helper exists only for heartbeat transport handling.
        Full message parsing belongs to Phase 3.5.
        """

        prefix = f'"{key}":"'
        start = payload.find(prefix)

        if start < 0:
            return ""

        value_start = start + len(prefix)

        result: list[str] = []
        escaped = False

        for character in payload[value_start:]:
            if escaped:
                result.append(character)
                escaped = False
                continue

            if character == "\\":
                escaped = True
                continue

            if character == '"':
                return "".join(result)

            result.append(character)

        return "".join(result)

    @staticmethod
    def _escape_json_string(value: str) -> str:
        """Escape a string using the same subset as the C++ serializer."""

        return (
            value.replace("\\", "\\\\")
            .replace('"', '\\"')
            .replace("\n", "\\n")
            .replace("\r", "\\r")
            .replace("\t", "\\t")
        )

    @staticmethod
    def _send_all(
        current_socket: socket.socket,
        data: bytes,
    ) -> None:
        """Send all bytes, handling partial TCP writes."""

        total_sent = 0

        while total_sent < len(data):
            sent = current_socket.send(
                data[total_sent:]
            )

            if sent == 0:
                raise ConnectionError(
                    "socket connection closed during send"
                )

            total_sent += sent

    def _mark_disconnected(self) -> None:
        """Mark the client disconnected and invoke its callback once."""

        should_notify = False

        with self._state_lock:
            if self._connected:
                self._connected = False
                should_notify = True

        if should_notify and self.on_disconnect is not None:
            self.on_disconnect()

    def _close_socket(self) -> None:
        """Close the current socket safely."""

        with self._send_lock:
            current_socket = self._socket
            self._socket = None

        if current_socket is None:
            return

        try:
            current_socket.shutdown(
                socket.SHUT_RDWR
            )
        except OSError:
            pass

        try:
            current_socket.close()
        except OSError:
            pass
