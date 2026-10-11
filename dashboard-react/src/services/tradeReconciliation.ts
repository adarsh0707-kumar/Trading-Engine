import type { Trade } from "../types";

export function mergeRecentTrades(
  snapshotTrades: readonly Trade[],
  liveTrades: readonly Trade[],
  limit: number,
): Trade[] {
  const mergedById = new Map<string, Trade>();
  for (const trade of snapshotTrades) mergedById.set(trade.tradeId, trade);
  // Prefer the WebSocket copy when the same execution exists in both sources.
  for (const trade of liveTrades) mergedById.set(trade.tradeId, trade);

  return [...mergedById.values()]
    .sort((left, right) => {
      const leftTime = Date.parse(left.timestamp);
      const rightTime = Date.parse(right.timestamp);
      if (!Number.isFinite(leftTime)) return Number.isFinite(rightTime) ? 1 : 0;
      if (!Number.isFinite(rightTime)) return -1;
      return rightTime - leftTime;
    })
    .slice(0, Math.max(0, limit));
}
