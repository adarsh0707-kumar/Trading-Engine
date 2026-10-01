import type { TradesProvider, TradesState } from "./trades.types.ts";

export function createTradesProvider(): TradesProvider {
  return {
    getTrades(): TradesState | null {
      return null;
    },
  };
}
