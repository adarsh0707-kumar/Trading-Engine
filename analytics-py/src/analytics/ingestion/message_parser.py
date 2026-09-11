"""Parse trading-engine transport messages into analytics domain models."""

from __future__ import annotations

import json
from datetime import datetime
from decimal import Decimal, InvalidOperation
from typing import Any

from analytics.models import Tick, Trade


class MessageParseError(ValueError):
    """Raised when an incoming trading-engine message cannot be parsed."""


class MessageParser:
    """Parse JSON transport messages into domain models.

    The socket transport delivers a complete JSON envelope as text.

    Expected transport envelope::

        {
            "type": "TRADE",
            "request_id": "...",
            "timestamp": "...",
            "payload": "{...}"
        }

    The ``payload`` field for TRADE messages is itself a JSON string.
    """

    SUPPORTED_TYPES = frozenset({"TRADE", "MARKET_TICK"})

    def parse(self, message: str) -> Trade | Tick:
        """Parse one complete transport message.

        Args:
            message: Complete UTF-8 JSON message received from SocketClient.

        Returns:
            A ``Trade`` or ``Tick`` domain model.

        Raises:
            MessageParseError: If the message is malformed or unsupported.
        """
        envelope = self._parse_json_object(message, "transport message")

        event_type = self._require_string(
            envelope,
            "type",
            "transport message",
        )

        if event_type not in self.SUPPORTED_TYPES:
            raise MessageParseError(
                f"unsupported message type: {event_type!r}"
            )

        if event_type == "TRADE":
            return self._parse_trade(envelope)

        return self._parse_tick(envelope)

    def parse_trade(self, message: str) -> Trade:
        """Parse a transport message and require a TRADE event."""
        parsed = self.parse(message)

        if not isinstance(parsed, Trade):
            raise MessageParseError(
                f"expected TRADE message, received {parsed.event_type!r}"
            )

        return parsed

    def parse_tick(self, message: str) -> Tick:
        """Parse a transport message and require a MARKET_TICK event."""
        parsed = self.parse(message)

        if not isinstance(parsed, Tick):
            raise MessageParseError(
                f"expected MARKET_TICK message, received {parsed.event_type!r}"
            )

        return parsed

    def _parse_trade(self, envelope: dict[str, Any]) -> Trade:
        """Build a Trade model from a TRADE envelope."""
        event_id = self._require_string(
            envelope,
            "request_id",
            "TRADE envelope",
        )
        timestamp = self._parse_timestamp(
            self._require_string(
                envelope,
                "timestamp",
                "TRADE envelope",
            )
        )
        payload = self._parse_payload(envelope)

        return Trade(
            event_id=event_id,
            event_type="TRADE",
            trade_id=event_id,
            symbol=self._require_string(
                payload,
                "symbol",
                "TRADE payload",
            ),
            price=self._parse_decimal(
                payload,
                "price",
                "TRADE payload",
            ),
            quantity=self._parse_positive_int(
                payload,
                "quantity",
                "TRADE payload",
            ),
            timestamp=timestamp,
            buy_order_id=self._require_string(
                payload,
                "taker_order_id",
                "TRADE payload",
            ),
            sell_order_id=self._require_string(
                payload,
                "maker_order_id",
                "TRADE payload",
            ),
        )

    def _parse_tick(self, envelope: dict[str, Any]) -> Tick:
        """Build a Tick model from a MARKET_TICK envelope."""
        event_id = self._require_string(
            envelope,
            "request_id",
            "MARKET_TICK envelope",
        )
        timestamp = self._parse_timestamp(
            self._require_string(
                envelope,
                "timestamp",
                "MARKET_TICK envelope",
            )
        )
        payload = self._parse_payload(envelope)

        return Tick(
            event_id=event_id,
            event_type="MARKET_TICK",
            symbol=self._require_string(
                payload,
                "symbol",
                "MARKET_TICK payload",
            ),
            price=self._parse_decimal(
                payload,
                "price",
                "MARKET_TICK payload",
            ),
            quantity=self._parse_positive_int(
                payload,
                "quantity",
                "MARKET_TICK payload",
            ),
            timestamp=timestamp,
        )

    @staticmethod
    def _parse_json_object(
        value: str,
        context: str,
    ) -> dict[str, Any]:
        """Parse a JSON object."""
        if not isinstance(value, str):
            raise MessageParseError(
                f"{context} must be a string"
            )

        try:
            parsed = json.loads(value)
        except json.JSONDecodeError as exc:
            raise MessageParseError(
                f"invalid JSON in {context}: {exc.msg}"
            ) from exc

        if not isinstance(parsed, dict):
            raise MessageParseError(
                f"{context} must decode to a JSON object"
            )

        return parsed

    @classmethod
    def _parse_payload(
        cls,
        envelope: dict[str, Any],
    ) -> dict[str, Any]:
        """Parse the nested JSON payload."""
        payload = envelope.get("payload")

        if not isinstance(payload, str):
            raise MessageParseError(
                "payload must be a JSON string"
            )

        return cls._parse_json_object(
            payload,
            "message payload",
        )

    @staticmethod
    def _require_string(
        data: dict[str, Any],
        field: str,
        context: str,
    ) -> str:
        """Read a required non-empty string field."""
        value = data.get(field)

        if not isinstance(value, str):
            raise MessageParseError(
                f"{context}.{field} must be a string"
            )

        if not value:
            raise MessageParseError(
                f"{context}.{field} must not be empty"
            )

        return value

    @staticmethod
    def _parse_decimal(
        data: dict[str, Any],
        field: str,
        context: str,
    ) -> Decimal:
        """Read a positive decimal field without binary float conversion."""
        value = data.get(field)

        if isinstance(value, bool) or value is None:
            raise MessageParseError(
                f"{context}.{field} must be numeric"
            )

        try:
            decimal_value = Decimal(str(value))
        except (InvalidOperation, ValueError) as exc:
            raise MessageParseError(
                f"{context}.{field} must be a valid decimal"
            ) from exc

        if decimal_value <= 0:
            raise MessageParseError(
                f"{context}.{field} must be positive"
            )

        return decimal_value

    @staticmethod
    def _parse_positive_int(
        data: dict[str, Any],
        field: str,
        context: str,
    ) -> int:
        """Read a required positive integer."""
        value = data.get(field)

        if isinstance(value, bool) or not isinstance(value, int):
            raise MessageParseError(
                f"{context}.{field} must be an integer"
            )

        if value <= 0:
            raise MessageParseError(
                f"{context}.{field} must be positive"
            )

        return value

    @staticmethod
    def _parse_timestamp(value: str) -> datetime:
        """Parse an ISO-8601 timestamp."""
        normalized = value

        if normalized.endswith("Z"):
            normalized = normalized[:-1] + "+00:00"

        try:
            timestamp = datetime.fromisoformat(normalized)
        except ValueError as exc:
            raise MessageParseError(
                f"timestamp must be a valid ISO-8601 value: {value!r}"
            ) from exc

        if timestamp.tzinfo is None:
            raise MessageParseError(
                "timestamp must include timezone information"
            )

        return timestamp


__all__ = [
    "MessageParseError",
    "MessageParser",
]
