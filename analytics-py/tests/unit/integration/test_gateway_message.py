import json
from datetime import datetime, timezone
from decimal import Decimal

import pytest

from analytics.integration.gateway_message import (
    ANALYTICS_PROTOCOL_VERSION,
    GatewayMessageParseError,
    GatewayTradeMessage,
)

VALID_MESSAGE = {
    "version": ANALYTICS_PROTOCOL_VERSION,
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
}


def test_parses_valid_gateway_trade() -> None:
    message = GatewayTradeMessage.parse(json.dumps(VALID_MESSAGE))

    assert message.version == 1
    assert message.event_id == "trade-00000001-buy-1-sell-1"
    assert message.request_id == message.event_id
    assert message.timestamp == datetime(
        2026,
        10,
        2,
        12,
        0,
        1,
        tzinfo=timezone.utc,
    )
    assert message.trade.symbol == "SIM"
    assert message.trade.price == Decimal("100.25")
    assert message.trade.quantity == 10
    assert message.trade.taker_side == "BUY"


def test_serializes_normalized_contract_representation() -> None:
    message = GatewayTradeMessage.parse(json.dumps(VALID_MESSAGE))

    assert message.to_dict() == {
        "version": 1,
        "type": "TRADE",
        "event_id": "trade-00000001-buy-1-sell-1",
        "request_id": "trade-00000001-buy-1-sell-1",
        "timestamp": "2026-10-02T12:00:01+00:00",
        "payload": {
            "buy_order_id": "buy-1",
            "maker_order_id": "sell-1",
            "price": "100.25",
            "quantity": 10,
            "sell_order_id": "sell-1",
            "symbol": "SIM",
            "taker_order_id": "buy-1",
            "taker_side": "BUY",
        },
    }


@pytest.mark.parametrize(
    ("label", "patch"),
    [
        ("version", {"version": 2}),
        ("type", {"type": "RISK_EVENT"}),
        ("event id", {"event_id": ""}),
        ("request id", {"request_id": ""}),
        ("mismatched ids", {"event_id": "different"}),
        ("timestamp", {"timestamp": "not-a-timestamp"}),
        ("payload type", {"payload": {"symbol": "SIM"}}),
    ],
)
def test_rejects_invalid_envelopes(
    label: str,
    patch: dict[str, object],
) -> None:
    message = {**VALID_MESSAGE, **patch}

    with pytest.raises(GatewayMessageParseError, match=""):
        GatewayTradeMessage.parse(json.dumps(message))


def test_rejects_invalid_trade_payload() -> None:
    payload = json.loads(VALID_MESSAGE["payload"])
    payload["taker_side"] = "HOLD"

    message = {
        **VALID_MESSAGE,
        "payload": json.dumps(payload),
    }

    with pytest.raises(GatewayMessageParseError, match="TRADE payload"):
        GatewayTradeMessage.parse(json.dumps(message))
