import { describe, expect, test } from "bun:test";
import type { Trade } from "../types";
import { mergeRecentTrades } from "./tradeReconciliation";

function trade(tradeId: string, timestamp: string, price: number): Trade {
  return {
    tradeId,
    symbol: "SIM",
    price,
    quantity: 1,
    takerSide: "buy",
    timestamp,
  };
}

describe("mergeRecentTrades", () => {
  test("deduplicates by trade ID and prefers the live execution", () => {
    const snapshot = [
      trade("trade-1", "2026-10-11T10:00:00.000Z", 100),
      trade("trade-2", "2026-10-11T10:01:00.000Z", 101),
    ];
    const live = [
      trade("trade-1", "2026-10-11T10:00:00.000Z", 100.5),
      trade("trade-3", "2026-10-11T10:02:00.000Z", 102),
    ];

    expect(mergeRecentTrades(snapshot, live, 25)).toEqual([
      trade("trade-3", "2026-10-11T10:02:00.000Z", 102),
      trade("trade-2", "2026-10-11T10:01:00.000Z", 101),
      trade("trade-1", "2026-10-11T10:00:00.000Z", 100.5),
    ]);
  });

  test("keeps the newest entries within the requested limit", () => {
    const snapshot = [
      trade("old", "2026-10-11T09:00:00.000Z", 99),
      trade("newest", "2026-10-11T10:02:00.000Z", 102),
    ];
    const live = [trade("middle", "2026-10-11T10:01:00.000Z", 101)];

    expect(mergeRecentTrades(snapshot, live, 2).map((item) => item.tradeId))
      .toEqual(["newest", "middle"]);
  });

  test("handles invalid timestamps without dropping valid trade ordering", () => {
    const snapshot = [
      trade("invalid", "not-a-timestamp", 99),
      trade("valid", "2026-10-11T10:00:00.000Z", 100),
    ];

    expect(mergeRecentTrades(snapshot, [], 25).map((item) => item.tradeId))
      .toEqual(["valid", "invalid"]);
  });
});
