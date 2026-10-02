import { describe, expect, test } from "bun:test";

import {
  normalizeEngineEvent,
  UnsupportedEngineEventError,
} from "../src/engine-protocol/engine-event.ts";

function createTradeEvent() {
  return {
    type: "TRADE" as const,
    eventId: "trade-42-buy-sell",
    requestId: "trade-42-buy-sell",
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
  };
}

describe("normalizeEngineEvent", () => {
  test("dispatches TRADE events to typed normalization", () => {
    const event = normalizeEngineEvent(
      createTradeEvent(),
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

  test("rejects HELLO until a typed HELLO payload contract exists", () => {
    expect(() =>
      normalizeEngineEvent({
        type: "HELLO",
        eventId: "hello-1",
        requestId: "hello-1",
        timestamp: "2026-10-01T12:00:00.000Z",
        payload: "gateway",
      }),
    ).toThrow(
      new UnsupportedEngineEventError("HELLO"),
    );
  });

  test("rejects HEARTBEAT until a typed HEARTBEAT payload contract exists", () => {
    expect(() =>
      normalizeEngineEvent({
        type: "HEARTBEAT",
        eventId: "heartbeat-1",
        requestId: "heartbeat-1",
        timestamp: "2026-10-01T12:00:00.000Z",
        payload: "PING",
      }),
    ).toThrow(
      new UnsupportedEngineEventError("HEARTBEAT"),
    );
  });

  test("rejects ORDER until an engine ORDER payload contract exists", () => {
    expect(() =>
      normalizeEngineEvent({
        type: "ORDER",
        eventId: "order-1",
        requestId: "order-1",
        timestamp: "2026-10-01T12:00:00.000Z",
        payload: "{}",
      }),
    ).toThrow(
      new UnsupportedEngineEventError("ORDER"),
    );
  });

  test("rejects MARKET_DATA until an engine market-data contract exists", () => {
    expect(() =>
      normalizeEngineEvent({
        type: "MARKET_DATA",
        eventId: "market-1",
        requestId: "market-1",
        timestamp: "2026-10-01T12:00:00.000Z",
        payload: "{}",
      }),
    ).toThrow(
      new UnsupportedEngineEventError("MARKET_DATA"),
    );
  });

  test("rejects BOOK_SNAPSHOT until an engine book contract exists", () => {
    expect(() =>
      normalizeEngineEvent({
        type: "BOOK_SNAPSHOT",
        eventId: "book-1",
        requestId: "book-1",
        timestamp: "2026-10-01T12:00:00.000Z",
        payload: "{}",
      }),
    ).toThrow(
      new UnsupportedEngineEventError("BOOK_SNAPSHOT"),
    );
  });

  test("rejects ERROR until an engine error payload contract exists", () => {
    expect(() =>
      normalizeEngineEvent({
        type: "ERROR",
        eventId: "error-1",
        requestId: "error-1",
        timestamp: "2026-10-01T12:00:00.000Z",
        payload: "Invalid message",
      }),
    ).toThrow(
      new UnsupportedEngineEventError("ERROR"),
    );
  });

  test("rejects SHUTDOWN until a typed shutdown contract exists", () => {
    expect(() =>
      normalizeEngineEvent({
        type: "SHUTDOWN",
        eventId: "shutdown-1",
        requestId: "shutdown-1",
        timestamp: "2026-10-01T12:00:00.000Z",
        payload: "shutdown",
      }),
    ).toThrow(
      new UnsupportedEngineEventError("SHUTDOWN"),
    );
  });
});
