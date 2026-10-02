import { describe, expect, test } from "bun:test";

import {
  EngineMessageValidationError,
} from "../src/engine-protocol/engine-message.ts";
import {
  normalizeTradeEvent,
} from "../src/engine-protocol/engine-trade.ts";

function createTradeEvent(
  payload: string,
) {
  return {
    type: "TRADE" as const,
    eventId: "trade-42-buy-sell",
    requestId: "trade-42-buy-sell",
    timestamp: "2026-10-01T12:00:00.000Z",
    payload,
  };
}

const validPayload = JSON.stringify({
  symbol: "SIM",
  price: 100.25,
  quantity: 10,
  taker_order_id: "SIM-00000042",
  maker_order_id: "SIM-00000017",
  taker_side: "BUY",
  buy_order_id: "SIM-00000042",
  sell_order_id: "SIM-00000017",
});

describe("normalizeTradeEvent", () => {
  test("normalizes the complete engine trade payload", () => {
    const event = normalizeTradeEvent(
      createTradeEvent(validPayload),
    );

    expect(event).toEqual({
      type: "TRADE",
      eventId: "trade-42-buy-sell",
      tradeId: "trade-42-buy-sell",
      requestId: "trade-42-buy-sell",
      timestamp: "2026-10-01T12:00:00.000Z",
      payload: {
        symbol: "SIM",
        price: 100.25,
        quantity: 10,
        takerOrderId: "SIM-00000042",
        makerOrderId: "SIM-00000017",
        takerSide: "BUY",
        buyOrderId: "SIM-00000042",
        sellOrderId: "SIM-00000017",
      },
    });
  });

  test("preserves the engine trade id from request_id", () => {
    const event = normalizeTradeEvent(
      createTradeEvent(validPayload),
    );

    expect(event.tradeId).toBe(
      "trade-42-buy-sell",
    );

    expect(event.requestId).toBe(
      "trade-42-buy-sell",
    );
  });

  test("supports SELL taker side", () => {
    const payload = JSON.stringify({
      symbol: "SIM",
      price: 101,
      quantity: 3,
      taker_order_id: "SIM-00000017",
      maker_order_id: "SIM-00000042",
      taker_side: "SELL",
      buy_order_id: "SIM-00000042",
      sell_order_id: "SIM-00000017",
    });

    const event = normalizeTradeEvent(
      createTradeEvent(payload),
    );

    expect(event.payload.takerSide).toBe("SELL");
  });

  test("rejects invalid JSON", () => {
    expect(() =>
      normalizeTradeEvent(
        createTradeEvent("{invalid"),
      ),
    ).toThrow(
      new EngineMessageValidationError(
        "TRADE payload contains invalid JSON",
      ),
    );
  });

  test("rejects a non-object payload", () => {
    expect(() =>
      normalizeTradeEvent(
        createTradeEvent("[]"),
      ),
    ).toThrow(
      new EngineMessageValidationError(
        "TRADE payload must be a JSON object",
      ),
    );
  });

  test("rejects a missing symbol", () => {
    const payload = JSON.stringify({
      price: 100,
      quantity: 10,
      taker_order_id: "taker-1",
      maker_order_id: "maker-1",
      taker_side: "BUY",
      buy_order_id: "buy-1",
      sell_order_id: "sell-1",
    });

    expect(() =>
      normalizeTradeEvent(
        createTradeEvent(payload),
      ),
    ).toThrow(
      new EngineMessageValidationError(
        "TRADE payload field 'symbol' must be a non-empty string",
      ),
    );
  });

  test("rejects a non-positive price", () => {
    const payload = JSON.stringify({
      symbol: "SIM",
      price: 0,
      quantity: 10,
      taker_order_id: "taker-1",
      maker_order_id: "maker-1",
      taker_side: "BUY",
      buy_order_id: "buy-1",
      sell_order_id: "sell-1",
    });

    expect(() =>
      normalizeTradeEvent(
        createTradeEvent(payload),
      ),
    ).toThrow(
      new EngineMessageValidationError(
        "TRADE payload field 'price' must be a positive number",
      ),
    );
  });

  test("rejects a non-positive integer quantity", () => {
    const payload = JSON.stringify({
      symbol: "SIM",
      price: 100,
      quantity: 1.5,
      taker_order_id: "taker-1",
      maker_order_id: "maker-1",
      taker_side: "BUY",
      buy_order_id: "buy-1",
      sell_order_id: "sell-1",
    });

    expect(() =>
      normalizeTradeEvent(
        createTradeEvent(payload),
      ),
    ).toThrow(
      new EngineMessageValidationError(
        "TRADE payload field 'quantity' must be a positive integer",
      ),
    );
  });

  test("rejects an unsupported taker side", () => {
    const payload = JSON.stringify({
      symbol: "SIM",
      price: 100,
      quantity: 10,
      taker_order_id: "taker-1",
      maker_order_id: "maker-1",
      taker_side: "HOLD",
      buy_order_id: "buy-1",
      sell_order_id: "sell-1",
    });

    expect(() =>
      normalizeTradeEvent(
        createTradeEvent(payload),
      ),
    ).toThrow(
      new EngineMessageValidationError(
        "TRADE payload field 'taker_side' must be BUY or SELL",
      ),
    );
  });

  test("rejects missing order identity", () => {
    const payload = JSON.stringify({
      symbol: "SIM",
      price: 100,
      quantity: 10,
      taker_order_id: "taker-1",
      maker_order_id: "maker-1",
      taker_side: "BUY",
      buy_order_id: "buy-1",
    });

    expect(() =>
      normalizeTradeEvent(
        createTradeEvent(payload),
      ),
    ).toThrow(
      new EngineMessageValidationError(
        "TRADE payload field 'sell_order_id' must be a non-empty string",
      ),
    );
  });

  test("rejects a non-TRADE event", () => {
    expect(() =>
      normalizeTradeEvent({
        type: "HEARTBEAT",
        eventId: "heartbeat-1",
        requestId: "heartbeat-1",
        timestamp: "2026-10-01T12:00:00.000Z",
        payload: "PING",
      }),
    ).toThrow(
      new EngineMessageValidationError(
        "Expected TRADE event but received HEARTBEAT",
      ),
    );
  });
});
