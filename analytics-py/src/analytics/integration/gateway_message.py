"""Gateway-to-analytics wire contract.

This module defines the Phase 4.6.1 contract only. It does not open sockets
or change the analytics runtime. The existing MessageParser remains the
authoritative TRADE domain parser.
"""

from __future__ import annotations

import json
from dataclasses import dataclass
from datetime import datetime
from decimal import Decimal
from typing import Any

from analytics.ingestion.message_parser import MessageParser
from analytics.models import AnalyticsResult, RiskEvent, Trade

ANALYTICS_PROTOCOL_VERSION = 1
SUPPORTED_MESSAGE_TYPE = "TRADE"
ANALYTICS_UPDATE_MESSAGE_TYPE = "ANALYTICS_UPDATE"
RISK_EVENT_MESSAGE_TYPE = "RISK_EVENT"


class GatewayMessageParseError(ValueError):
    """Raised when a Gateway analytics message violates the wire contract."""


@dataclass(frozen=True, slots=True)
class GatewayTradeMessage:
    """Validated Gateway TRADE envelope."""

    version: int
    event_id: str
    request_id: str
    timestamp: datetime
    trade: Trade

    @classmethod
    def parse(cls, message: str) -> GatewayTradeMessage:
        if not isinstance(message, str):
            raise GatewayMessageParseError(
                "Gateway analytics message must be a string"
            )

        try:
            envelope = json.loads(message)
        except json.JSONDecodeError as exc:
            raise GatewayMessageParseError(
                f"invalid JSON: {exc.msg}"
            ) from exc

        if not isinstance(envelope, dict):
            raise GatewayMessageParseError(
                "Gateway analytics message must decode to a JSON object"
            )

        if envelope.get("version") != ANALYTICS_PROTOCOL_VERSION:
            raise GatewayMessageParseError(
                f"unsupported analytics protocol version: {envelope.get('version')!r}"
            )

        if envelope.get("type") != SUPPORTED_MESSAGE_TYPE:
            raise GatewayMessageParseError(
                f"unsupported analytics message type: {envelope.get('type')!r}"
            )

        event_id = _require_string(envelope, "event_id", "Gateway envelope")
        request_id = _require_string(
            envelope,
            "request_id",
            "Gateway envelope",
        )

        if event_id != request_id:
            raise GatewayMessageParseError(
                "event_id must equal request_id for TRADE messages"
            )

        timestamp = _parse_timestamp(
            _require_string(
                envelope,
                "timestamp",
                "Gateway envelope",
            )
        )

        payload = envelope.get("payload")
        if not isinstance(payload, str):
            raise GatewayMessageParseError(
                "Gateway TRADE payload must be a JSON string"
            )

        try:
            trade = MessageParser().parse_trade(
                json.dumps(
                    {
                        "type": "TRADE",
                        "request_id": request_id,
                        "timestamp": timestamp.isoformat(),
                        "payload": payload,
                    }
                )
            )
        except ValueError as exc:
            raise GatewayMessageParseError(
                f"invalid TRADE payload: {exc}"
            ) from exc

        if trade.event_id != event_id:
            raise GatewayMessageParseError(
                "TRADE payload identity does not match event_id"
            )

        return cls(
            version=ANALYTICS_PROTOCOL_VERSION,
            event_id=event_id,
            request_id=request_id,
            timestamp=timestamp,
            trade=trade,
        )

    def to_dict(self) -> dict[str, Any]:
        """Return the normalized contract representation."""

        return {
            "version": self.version,
            "type": SUPPORTED_MESSAGE_TYPE,
            "event_id": self.event_id,
            "request_id": self.request_id,
            "timestamp": self.timestamp.isoformat(),
            "payload": json.loads(self.trade_payload_json()),
        }

    def trade_payload_json(self) -> str:
        """Return the nested JSON-string payload expected on the wire."""

        payload = self.trade.to_dict()
        payload.pop("event_id", None)
        payload.pop("event_type", None)
        return json.dumps(
            payload,
            separators=(",", ":"),
            sort_keys=True,
        )



def serialize_analytics_update(result: AnalyticsResult) -> str:
    """Serialize an AnalyticsResult using the bidirectional Gateway contract."""
    payload = json.dumps(
        result.to_dict(),
        separators=(",", ":"),
        sort_keys=True,
    )
    return json.dumps(
        {
            "version": ANALYTICS_PROTOCOL_VERSION,
            "type": ANALYTICS_UPDATE_MESSAGE_TYPE,
            "event_id": result.event_id,
            "request_id": result.event_id,
            "timestamp": result.timestamp.isoformat(),
            "payload": payload,
        },
        separators=(",", ":"),
        sort_keys=True,
    )


def serialize_risk_event(event: RiskEvent) -> str:
    """Serialize a RiskEvent using the bidirectional Gateway contract."""
    payload = json.dumps(
        event.to_dict(),
        separators=(",", ":"),
        sort_keys=True,
    )
    return json.dumps(
        {
            "version": ANALYTICS_PROTOCOL_VERSION,
            "type": RISK_EVENT_MESSAGE_TYPE,
            "event_id": event.event_id,
            "request_id": event.event_id,
            "timestamp": event.timestamp.isoformat(),
            "payload": payload,
        },
        separators=(",", ":"),
        sort_keys=True,
    )

def _require_string(
    data: dict[str, Any],
    field: str,
    context: str,
) -> str:
    value = data.get(field)

    if not isinstance(value, str) or not value:
        raise GatewayMessageParseError(
            f"{context}.{field} must be a non-empty string"
        )

    return value


def _parse_timestamp(value: str) -> datetime:
    normalized = value[:-1] + "+00:00" if value.endswith("Z") else value

    try:
        timestamp = datetime.fromisoformat(normalized)
    except ValueError as exc:
        raise GatewayMessageParseError(
            f"timestamp must be valid ISO-8601: {value!r}"
        ) from exc

    if timestamp.tzinfo is None:
        raise GatewayMessageParseError(
            "timestamp must include timezone information"
        )

    return timestamp


__all__ = [
    "ANALYTICS_PROTOCOL_VERSION",
    "GatewayMessageParseError",
    "GatewayTradeMessage",
    "serialize_analytics_update",
    "serialize_risk_event",
]
