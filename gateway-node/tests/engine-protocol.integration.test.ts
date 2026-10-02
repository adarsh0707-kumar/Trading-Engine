import { describe, expect, test } from "bun:test";

import {
  createEngineProtocol,
} from "../src/engine-protocol/engine-protocol.ts";
import {
  normalizeEngineEvent,
} from "../src/engine-protocol/engine-event.ts";

function frameJson(
  value: unknown,
): Uint8Array {
  const payload = new TextEncoder().encode(
    JSON.stringify(value),
  );

  const frame = new Uint8Array(
    4 + payload.byteLength,
  );

  const view = new DataView(frame.buffer);

  view.setUint32(
    0,
    payload.byteLength,
    false,
  );

  frame.set(payload, 4);

  return frame;
}

function concat(
  first: Uint8Array,
  second: Uint8Array,
): Uint8Array {
  const result = new Uint8Array(
    first.byteLength + second.byteLength,
  );

  result.set(first);
  result.set(second, first.byteLength);

  return result;
}

describe("engine protocol integration", () => {
  test("decodes a C++-compatible TRADE frame into a typed trade event", () => {
    const protocol = createEngineProtocol();

    const frame = frameJson({
      type: "TRADE",
      request_id: "trade-42-buy-sell",
      timestamp: "2026-10-01T12:00:00.000Z",
      payload: JSON.stringify({
        symbol: "SIM",
        price: 100.25,
        quantity: 10,
        taker_order_id: "SIM-00000042",
        maker_order_id: "SIM-00000017",
        taker_side: "BUY",
        buy_order_id: "SIM-00000042",
        sell_order_id: "SIM-00000017",
      }),
    });

    const events = protocol.push(frame);

    expect(events).toHaveLength(1);

    const trade = normalizeEngineEvent(
      events[0]!,
    );

    expect(trade).toEqual({
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

  test("handles a frame split across multiple TCP chunks", () => {
    const protocol = createEngineProtocol();

    const frame = frameJson({
      type: "TRADE",
      request_id: "trade-43-sell-buy",
      timestamp: "2026-10-01T12:01:00.000Z",
      payload: JSON.stringify({
        symbol: "SIM",
        price: 101.5,
        quantity: 3,
        taker_order_id: "SIM-00000017",
        maker_order_id: "SIM-00000043",
        taker_side: "SELL",
        buy_order_id: "SIM-00000043",
        sell_order_id: "SIM-00000017",
      }),
    });

    const splitPoint = 7;

    const first = frame.slice(
      0,
      splitPoint,
    );

    const second = frame.slice(
      splitPoint,
    );

    expect(protocol.push(first)).toEqual([]);

    const events = protocol.push(second);

    expect(events).toHaveLength(1);

    const trade = normalizeEngineEvent(
      events[0]!,
    );

    expect(trade.type).toBe("TRADE");
    expect(trade.tradeId).toBe(
      "trade-43-sell-buy",
    );
    expect(trade.payload.takerSide).toBe(
      "SELL",
    );
    expect(trade.payload.price).toBe(101.5);
    expect(trade.payload.quantity).toBe(3);
  });

  test("decodes multiple engine events from one TCP chunk", () => {
    const protocol = createEngineProtocol();

    const first = frameJson({
      type: "TRADE",
      request_id: "trade-44-buy-sell",
      timestamp: "2026-10-01T12:02:00.000Z",
      payload: JSON.stringify({
        symbol: "SIM",
        price: 102,
        quantity: 2,
        taker_order_id: "buy-44",
        maker_order_id: "sell-44",
        taker_side: "BUY",
        buy_order_id: "buy-44",
        sell_order_id: "sell-44",
      }),
    });

    const second = frameJson({
      type: "TRADE",
      request_id: "trade-45-sell-buy",
      timestamp: "2026-10-01T12:03:00.000Z",
      payload: JSON.stringify({
        symbol: "SIM",
        price: 103,
        quantity: 4,
        taker_order_id: "sell-45",
        maker_order_id: "buy-45",
        taker_side: "SELL",
        buy_order_id: "buy-45",
        sell_order_id: "sell-45",
      }),
    });

    const events = protocol.push(
      concat(first, second),
    );

    expect(events).toHaveLength(2);

    const firstTrade = normalizeEngineEvent(
      events[0]!,
    );

    const secondTrade = normalizeEngineEvent(
      events[1]!,
    );

    expect(firstTrade.tradeId).toBe(
      "trade-44-buy-sell",
    );

    expect(secondTrade.tradeId).toBe(
      "trade-45-sell-buy",
    );
  });

  test("rejects malformed engine JSON at the protocol boundary", () => {
    const protocol = createEngineProtocol();

    const payload = new TextEncoder().encode(
      "{invalid-json",
    );

    const frame = new Uint8Array(
      4 + payload.byteLength,
    );

    new DataView(frame.buffer).setUint32(
      0,
      payload.byteLength,
      false,
    );

    frame.set(payload, 4);

    expect(() =>
      protocol.push(frame),
    ).toThrow(
      "Engine frame contains invalid JSON",
    );
  });
});
