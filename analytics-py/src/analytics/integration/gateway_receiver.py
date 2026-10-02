"""TCP receiver for Gateway-to-analytics TRADE messages.

The Gateway is the TCP client for this side of the integration. This receiver
owns only transport concerns: listening, framing, connection lifecycle, and
forwarding complete payloads to the analytics service callback. Contract and
business parsing remain in the integration contract and existing analytics
pipeline.
"""

from __future__ import annotations

import logging
import socket
import struct
import threading
from collections.abc import Callable


logger = logging.getLogger(__name__)


class GatewayReceiverProtocolError(Exception):
    """Raised when an inbound Gateway frame violates the transport protocol."""


class GatewayAnalyticsReceiver:
    """Receive framed Gateway analytics messages over TCP."""

    HEADER_SIZE = 4
    MAX_PAYLOAD_SIZE = 1024 * 1024

    def __init__(
        self,
        host: str,
        port: int,
        *,
        max_payload_size: int = MAX_PAYLOAD_SIZE,
        on_message: Callable[[str], None] | None = None,
        on_connect: Callable[[], None] | None = None,
        on_disconnect: Callable[[], None] | None = None,
    ) -> None:
        if not host:
            raise ValueError("host must not be empty")
        if not 1 <= port <= 65535:
            raise ValueError("port must be between 1 and 65535")
        if max_payload_size <= 0:
            raise ValueError("max_payload_size must be positive")

        self.host = host
        self.port = port
        self.max_payload_size = max_payload_size
        self.on_message = on_message
        self.on_connect = on_connect
        self.on_disconnect = on_disconnect

        self._server: socket.socket | None = None
        self._client: socket.socket | None = None
        self._thread: threading.Thread | None = None
        self._running = False
        self._state_lock = threading.Lock()
        self._client_lock = threading.Lock()
        self._stop_event = threading.Event()

    def start(self) -> None:
        """Start the background Gateway receiver."""
        with self._state_lock:
            if self._running:
                return
            self._running = True

        self._stop_event.clear()
        self._thread = threading.Thread(
            target=self._run,
            name="gateway-analytics-receiver",
            daemon=True,
        )
        self._thread.start()

    def stop(self) -> None:
        """Stop the receiver and close any active connection."""
        with self._state_lock:
            self._running = False

        self._stop_event.set()
        self._close_client()
        self._close_server()

        thread = self._thread
        if thread is not None and thread is not threading.current_thread():
            thread.join(timeout=2.0)

        self._thread = None

    def is_running(self) -> bool:
        """Return whether the receiver lifecycle is running."""
        with self._state_lock:
            return self._running

    def is_connected(self) -> bool:
        """Return whether a Gateway TCP connection is active."""
        with self._client_lock:
            return self._client is not None

    def send(self, payload: str) -> None:
        """Send one framed analytics result to the connected Gateway."""
        if not isinstance(payload, str):
            raise TypeError("payload must be a string")

        encoded = payload.encode("utf-8")
        if len(encoded) > self.max_payload_size:
            raise GatewayReceiverProtocolError(
                "outbound payload exceeds maximum frame size"
            )

        frame = struct.pack(">I", len(encoded)) + encoded

        with self._client_lock:
            client = self._client
            if client is None:
                raise ConnectionError("Gateway is not connected")

            try:
                client.sendall(frame)
            except OSError as exc:
                raise ConnectionError(
                    "failed to send analytics result to Gateway"
                ) from exc

    def _run(self) -> None:
        try:
            self._server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self._server.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            self._server.bind((self.host, self.port))
            self._server.listen(1)
            self._server.settimeout(0.5)

            logger.info(
                "gateway_receiver_listening host=%s port=%d",
                self.host,
                self.port,
            )

            while not self._stop_event.is_set():
                try:
                    client, address = self._server.accept()
                except socket.timeout:
                    continue
                except OSError:
                    if self._stop_event.is_set():
                        break
                    raise

                if self._stop_event.is_set():
                    client.close()
                    break

                self._accept_client(client, address)
                try:
                    self._receive_client(client)
                except GatewayReceiverProtocolError as exc:
                    logger.error(
                        "gateway_receiver_protocol_error host=%s port=%d error=%s",
                        self.host,
                        self.port,
                        exc,
                    )
                finally:
                    self._close_client()
                    self._notify_disconnect()

        except OSError as exc:
            if not self._stop_event.is_set():
                logger.error(
                    "gateway_receiver_error host=%s port=%d error=%s",
                    self.host,
                    self.port,
                    exc,
                )
        finally:
            self._close_client()
            self._close_server()

    def _accept_client(
        self,
        client: socket.socket,
        address: tuple[str, int],
    ) -> None:
        client.settimeout(0.5)
        with self._client_lock:
            self._client = client

        logger.info(
            "gateway_connected host=%s port=%d peer=%s:%d",
            self.host,
            self.port,
            address[0],
            address[1],
        )
        self._notify_connect()

    def _receive_client(self, client: socket.socket) -> None:
        buffer = bytearray()

        while not self._stop_event.is_set():
            try:
                chunk = client.recv(8192)
            except socket.timeout:
                continue
            except OSError:
                return

            if not chunk:
                return

            buffer.extend(chunk)

            for payload in self._extract_frames(buffer):
                self._notify_message(payload)

    def _extract_frames(self, buffer: bytearray) -> list[str]:
        payloads: list[str] = []

        while True:
            if len(buffer) < self.HEADER_SIZE:
                break

            payload_size = struct.unpack(
                ">I",
                buffer[: self.HEADER_SIZE],
            )[0]

            if payload_size > self.max_payload_size:
                raise GatewayReceiverProtocolError(
                    "received payload exceeds maximum frame size"
                )

            total_size = self.HEADER_SIZE + payload_size
            if len(buffer) < total_size:
                break

            payload_bytes = bytes(buffer[self.HEADER_SIZE : total_size])
            del buffer[:total_size]

            try:
                payloads.append(payload_bytes.decode("utf-8"))
            except UnicodeDecodeError as exc:
                raise GatewayReceiverProtocolError(
                    "received payload is not valid UTF-8"
                ) from exc

        return payloads

    def _notify_message(self, payload: str) -> None:
        if self.on_message is None:
            return

        try:
            self.on_message(payload)
        except Exception:
            logger.exception("gateway_receiver_message_callback_failed")

    def _notify_connect(self) -> None:
        if self.on_connect is None:
            return

        try:
            self.on_connect()
        except Exception:
            logger.exception("gateway_receiver_connect_callback_failed")

    def _notify_disconnect(self) -> None:
        if self.on_disconnect is None:
            return

        try:
            self.on_disconnect()
        except Exception:
            logger.exception("gateway_receiver_disconnect_callback_failed")

    def _close_client(self) -> None:
        with self._client_lock:
            client = self._client
            self._client = None

        if client is None:
            return

        try:
            client.shutdown(socket.SHUT_RDWR)
        except OSError:
            pass

        try:
            client.close()
        except OSError:
            pass

    def _close_server(self) -> None:
        server = self._server
        self._server = None

        if server is None:
            return

        try:
            server.close()
        except OSError:
            pass


__all__ = [
    "GatewayAnalyticsReceiver",
    "GatewayReceiverProtocolError",
]
