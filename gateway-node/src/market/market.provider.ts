import type { MarketProvider, MarketState } from "./market.types.ts";

export function createMarketProvider(): MarketProvider {
  return {
    getMarket(): MarketState | null {
      return null;
    },
  };
}
