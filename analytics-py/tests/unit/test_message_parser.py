"""Unit tests for the trading-engine message parser."""

from __future__ import annotations

import json
from datetime import timezone
from decimal import Decimal

import pytest

from analytics.ingestion import MessageParseError, MessageParser
from analytics.models import Tick, Trade



def _trade_message(taker_side: str = "BUY") -> str:

    return json.dumps(
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

                    "taker_side": taker_side,

                },
                separators=(",", ":"),
            ),
        },
        separators=(",", ":"),
    )


def _tick_message() -> str:
    return json.dumps(
        {
            "type": "MARKET_TICK",
            "request_id": "tick-SIM-00000001",
            "timestamp": "2026-09-10T00:00:01Z",
            "payload": json.dumps(
                {
                    "symbol": "SIM",
                    "price": "101.25",
                    "quantity": 5,
                },
                separators=(",", ":"),
            ),
        },
        separators=(",", ":"),
    )


def test_parse_trade_from_cxx_wire_message() -> None:
    parser = MessageParser()

    trade = parser.parse(_trade_message())

    assert isinstance(trade, Trade)
    assert trade.event_id == "trade-SIM-00000001-SIM-00000002"
    assert trade.event_type == "TRADE"
    assert trade.trade_id == "trade-SIM-00000001-SIM-00000002"
    assert trade.symbol == "SIM"
    assert trade.price == Decimal("98.57")
    assert trade.quantity == 3

    assert trade.taker_side == "BUY"

    assert trade.buy_order_id == "SIM-00000001"
    assert trade.sell_order_id == "SIM-00000002"
    assert trade.timestamp.tzinfo == timezone.utc



def test_sell_taker_maps_maker_to_the_buy_side() -> None:
    trade = MessageParser().parse_trade(_trade_message("SELL"))

    assert trade.taker_side == "SELL"
    assert trade.buy_order_id == "SIM-00000002"
    assert trade.sell_order_id == "SIM-00000001"


def test_parse_rejects_unknown_taker_side() -> None:
    message = json.loads(_trade_message())
    payload = json.loads(message["payload"])
    payload["taker_side"] = "LONG"
    message["payload"] = json.dumps(payload)

    with pytest.raises(MessageParseError, match="taker_side must be BUY or SELL"):
        MessageParser().parse(json.dumps(message))



def test_parse_tick() -> None:
    parser = MessageParser()

    tick = parser.parse(_tick_message())

    assert isinstance(tick, Tick)
    assert tick.event_id == "tick-SIM-00000001"
    assert tick.event_type == "MARKET_TICK"
    assert tick.symbol == "SIM"
    assert tick.price == Decimal("101.25")
    assert tick.quantity == 5
    assert tick.timestamp.tzinfo == timezone.utc


def test_parse_trade_requires_trade_message() -> None:
    parser = MessageParser()

    with pytest.raises(MessageParseError, match="expected TRADE"):
        parser.parse_trade(_tick_message())


def test_parse_tick_requires_tick_message() -> None:
    parser = MessageParser()

    with pytest.raises(MessageParseError, match="expected MARKET_TICK"):
        parser.parse_tick(_trade_message())


@pytest.mark.parametrize(
    ("message", "error"),
    [
        ("not-json", "invalid JSON"),
        ("[]", "must decode to a JSON object"),
        (
            json.dumps(
                {
                    "type": "UNKNOWN",
                    "request_id": "1",
                    "timestamp": "2026-09-10T00:00:00Z",
                    "payload": "{}",
                }
            ),
            "unsupported message type",
        ),
        (
            json.dumps(
                {
                    "type": "TRADE",
                    "request_id": "",
                    "timestamp": "2026-09-10T00:00:00Z",
                    "payload": "{}",
                }
            ),
            "request_id must not be empty",
        ),
        (
            json.dumps(
                {
                    "type": "TRADE",
                    "request_id": "trade-1",
                    "timestamp": "2026-09-10T00:00:00Z",
                    "payload": "{}",
                }
            ),
            "payload.symbol must be a string",
        ),
    ],
)
def test_parse_rejects_invalid_messages(
    message: str,
    error: str,
) -> None:
    parser = MessageParser()

    with pytest.raises(MessageParseError, match=error):
        parser.parse(message)


def test_parse_rejects_invalid_price() -> None:
    message = json.loads(_trade_message())
    payload = json.loads(message["payload"])
    payload["price"] = 0
    message["payload"] = json.dumps(payload)

    with pytest.raises(MessageParseError, match="price must be positive"):
        MessageParser().parse(json.dumps(message))


def test_parse_rejects_invalid_quantity() -> None:
    message = json.loads(_trade_message())
    payload = json.loads(message["payload"])
    payload["quantity"] = -1
    message["payload"] = json.dumps(payload)

    with pytest.raises(MessageParseError, match="quantity must be positive"):
        MessageParser().parse(json.dumps(message))


def test_parse_rejects_invalid_timestamp() -> None:
    message = json.loads(_trade_message())
    message["timestamp"] = "not-a-timestamp"

    with pytest.raises(
        MessageParseError,
        match="timestamp must be a valid ISO-8601 value",
    ):
        MessageParser().parse(json.dumps(message))


def test_parse_rejects_timestamp_without_timezone() -> None:
    message = json.loads(_trade_message())
    message["timestamp"] = "2026-09-10T00:00:00"

    with pytest.raises(
        MessageParseError,
        match="timestamp must include timezone",
    ):
        MessageParser().parse(json.dumps(message))
