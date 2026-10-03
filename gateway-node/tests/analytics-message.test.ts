import { describe, expect, test } from "bun:test";

import {
  AnalyticsMessageValidationError,
  normalizeGatewayTradeMessage,
  serializeGatewayTradeMessage,
} from "../src/analytics/analytics-message.ts";

const validMessage = {
  version: 1,
  type: "TRADE" as const,
  event_id: "trade-00000001-buy-1-sell-1",
  request_id: "trade-00000001-buy-1-sell-1",
  timestamp: "2026-10-02T12:00:01.000Z",
  payload: JSON.stringify({
    trade_id: "trade-00000001-buy-1-sell-1",
    symbol: "SIM",
    price: 100.25,
    quantity: 10,
    taker_order_id: "buy-1",
    maker_order_id: "sell-1",
    taker_side: "BUY",
    buy_order_id: "buy-1",
    sell_order_id: "sell-1",
  }),
};

describe("gateway analytics message contract", () => {
  test("normalizes a valid TRADE message", () => {
    expect(normalizeGatewayTradeMessage(validMessage)).toEqual({
      version: 1,
      type: "TRADE",
      eventId: "trade-00000001-buy-1-sell-1",
      requestId: "trade-00000001-buy-1-sell-1",
      timestamp: "2026-10-02T12:00:01.000Z",
      payload: {
        tradeId: "trade-00000001-buy-1-sell-1",
        symbol: "SIM",
        price: 100.25,
        quantity: 10,
        takerOrderId: "buy-1",
        makerOrderId: "sell-1",
        takerSide: "BUY",
        buyOrderId: "buy-1",
        sellOrderId: "sell-1",
      },
    });
  });

  test("serializes the stable Python-compatible wire envelope", () => {
    const normalized = normalizeGatewayTradeMessage(validMessage);

    expect(JSON.parse(serializeGatewayTradeMessage(normalized))).toEqual({
      version: 1,
      type: "TRADE",
      event_id: "trade-00000001-buy-1-sell-1",
      request_id: "trade-00000001-buy-1-sell-1",
      timestamp: "2026-10-02T12:00:01.000Z",
      payload: JSON.stringify({
        trade_id: "trade-00000001-buy-1-sell-1",
        symbol: "SIM",
        price: 100.25,
        quantity: 10,
        taker_order_id: "buy-1",
        maker_order_id: "sell-1",
        taker_side: "BUY",
        buy_order_id: "buy-1",
        sell_order_id: "sell-1",
      }),
    });
  });

  test.each([
    ["unsupported version", { ...validMessage, version: 2 }],
    ["wrong type", { ...validMessage, type: "ANALYTICS_UPDATE" }],
    ["missing event id", { ...validMessage, event_id: "" }],
    [
      "mismatched ids",
      { ...validMessage, event_id: "different-event" },
    ],
    [
      "invalid timestamp",
      { ...validMessage, timestamp: "" },
    ],
    [
      "invalid price",
      {
        ...validMessage,
        payload: JSON.stringify({ ...JSON.parse(validMessage.payload as string), price: 0 }),
      },
    ],
    [
      "invalid quantity",
      {
        ...validMessage,
        payload: JSON.stringify({ ...JSON.parse(validMessage.payload as string), quantity: 0 }),
      },
    ],
    [
      "invalid side",
      {
        ...validMessage,
        payload: JSON.stringify({ ...JSON.parse(validMessage.payload as string), taker_side: "HOLD" }),
      },
    ],
  ])("rejects %s", (_, message) => {
    expect(() => normalizeGatewayTradeMessage(message)).toThrow(
      AnalyticsMessageValidationError,
    );
  });
});
