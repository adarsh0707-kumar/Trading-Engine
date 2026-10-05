import { describe, expect, test } from "bun:test";

import type { NormalizedTradeEvent } from "../src/engine-protocol/engine-trade.types.ts";
import { createLiveTradingState } from "../src/live-trading/live-trading-state.ts";

function createTradeEvent(
  overrides: Partial<NormalizedTradeEvent> = {},
): NormalizedTradeEvent {
  return {
    type: "TRADE",
    eventId: "trade-1",
    tradeId: "trade-1",
    requestId: "request-1",
    timestamp: "2026-10-05T12:00:00.000Z",
    payload: {
      symbol: "SIM",
      price: 100.25,
      quantity: 10,
      takerOrderId: "buy-1",
      makerOrderId: "sell-1",
      takerSide: "BUY",
      buyOrderId: "buy-1",
      sellOrderId: "sell-1",
    },
    ...overrides,
  };
}

describe("live trading state", () => {
  test("starts with no market state and empty trade history", () => {
    const state = createLiveTradingState();

    expect(state.getMarket()).toBeNull();
    expect(state.getTrades()).toEqual({
      trades: [],
    });
  });

  test("updates market state from a trade", () => {
    const state = createLiveTradingState();

    state.onTrade(createTradeEvent());

    expect(state.getMarket()).toEqual({
      symbol: "SIM",
      lastPrice: 100.25,
      lastQuantity: 10,
      timestamp: "2026-10-05T12:00:00.000Z",
    });
  });

  test("maps a trade event into the public trade shape", () => {
    const state = createLiveTradingState();

    state.onTrade(createTradeEvent());

    expect(state.getTrades()).toEqual({
      trades: [
        {
          tradeId: "trade-1",
          symbol: "SIM",
          price: 100.25,
          quantity: 10,
          takerSide: "buy",
          timestamp: "2026-10-05T12:00:00.000Z",
        },
      ],
    });
  });

  test("keeps newest trades first", () => {
    const state = createLiveTradingState();

    state.onTrade(createTradeEvent());

    state.onTrade(
      createTradeEvent({
        eventId: "trade-2",
        tradeId: "trade-2",
        requestId: "request-2",
        timestamp: "2026-10-05T12:01:00.000Z",
        payload: {
          ...createTradeEvent().payload,
          price: 101.5,
          quantity: 5,
          takerSide: "SELL",
        },
      }),
    );

    const trades = state.getTrades();

    expect(trades).not.toBeNull();
    if (trades === null) {
      throw new Error("Trade history unexpectedly unavailable");
    }

    expect(trades.trades.map((trade) => trade.tradeId)).toEqual([
      "trade-2",
      "trade-1",
    ]);
  });

  test("bounds trade history to the configured maximum", () => {
    const state = createLiveTradingState(2);

    for (let index = 1; index <= 3; index += 1) {
      state.onTrade(
        createTradeEvent({
          eventId: `trade-${index}`,
          tradeId: `trade-${index}`,
          requestId: `request-${index}`,
        }),
      );
    }

    const trades = state.getTrades();

    expect(trades).not.toBeNull();
    if (trades === null) {
      throw new Error("Trade history unexpectedly unavailable");
    }

    expect(trades.trades.map((trade) => trade.tradeId)).toEqual([
      "trade-3",
      "trade-2",
    ]);
  });

  test("rejects an invalid maximum trade count", () => {
    expect(() => createLiveTradingState(0)).toThrow(
      "maxTrades must be a positive integer",
    );

    expect(() => createLiveTradingState(-1)).toThrow(
      "maxTrades must be a positive integer",
    );

    expect(() => createLiveTradingState(1.5)).toThrow(
      "maxTrades must be a positive integer",
    );
  });
});
