"""Application entry point for the streaming analytics service."""

from __future__ import annotations

import logging
import signal
from threading import Event
from typing import Callable

from analytics.config.settings import Settings
from analytics.ingestion import MessageParseError, MessageParser, SocketClient
from analytics.models import Trade
from analytics.pipeline import AnalyticsPublisher, StreamingProcessor


logger = logging.getLogger(__name__)


class AnalyticsService:
    """Wire ingestion, parsing, processing, and publishing together."""

    def __init__(
        self,
        settings: Settings,
        *,
        publish_sink: Callable[[str], None] | None = None,
    ) -> None:
        self.settings = settings

        self.parser = MessageParser()
        self.processor = StreamingProcessor()

        if publish_sink is None:
            publish_sink = self._default_publish_sink

        self.publisher = AnalyticsPublisher(publish_sink)

        self.client = SocketClient(
            settings.engine_host,
            settings.engine_port,
            connect_timeout=settings.connect_timeout,
            receive_timeout=settings.receive_timeout,
            reconnect=settings.reconnect,
            reconnect_delay=settings.reconnect_delay,
            max_payload_size=settings.max_payload_size,
            on_message=self._handle_message,
            on_connect=self._handle_connect,
            on_disconnect=self._handle_disconnect,
        )

    def start(self) -> None:
        """Start the analytics service."""
        logger.info(
            "starting analytics service: engine=%s:%d",
            self.settings.engine_host,
            self.settings.engine_port,
        )

        self.client.start()

    def stop(self) -> None:
        """Stop the analytics service."""
        logger.info("stopping analytics service")
        self.client.stop()

    def _handle_message(self, message: str) -> None:
        """Parse and process one complete transport message."""
        try:
            event = self.parser.parse(message)
        except MessageParseError as exc:
            logger.warning("failed to parse incoming message: %s", exc)
            return

        if isinstance(event, Trade):
            try:
                result = self.processor.process_trade(event)
                self.publisher.publish(result)
            except (TypeError, ValueError) as exc:
                logger.warning(
                    "failed to process trade %s: %s",
                    event.event_id,
                    exc,
                )
            return

        logger.debug(
            "ignoring %s event for current analytics pipeline",
            event.event_type,
        )

    def _handle_connect(self) -> None:
        """Handle successful connection to the trading engine."""
        logger.info(
            "connected to trading engine at %s:%d",
            self.settings.engine_host,
            self.settings.engine_port,
        )

    def _handle_disconnect(self) -> None:
        """Handle trading-engine disconnection."""
        logger.warning("disconnected from trading engine")

    @staticmethod
    def _default_publish_sink(payload: str) -> None:
        """Log published analytics payloads until a downstream sink exists."""
        logger.info("analytics update: %s", payload)


def run(settings: Settings | None = None) -> None:
    """Run the analytics service until interrupted."""
    settings = settings or Settings.from_environment()

    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s %(levelname)s %(name)s: %(message)s",
    )

    service = AnalyticsService(settings)
    stop_event = Event()

    def _shutdown(signum: int, _frame: object) -> None:
        logger.info("received signal %d", signum)
        stop_event.set()

    signal.signal(signal.SIGINT, _shutdown)
    signal.signal(signal.SIGTERM, _shutdown)

    service.start()

    try:
        stop_event.wait()
    finally:
        service.stop()


def main() -> None:
    """CLI entry point."""
    run()


if __name__ == "__main__":
    main()
