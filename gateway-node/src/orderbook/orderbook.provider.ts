import type {
  OrderBookProvider,
  OrderBookState,
} from "./orderbook.types.ts";

export function createOrderBookProvider(): OrderBookProvider {
  return {
    getOrderBook(): OrderBookState | null {
      return null;
    },
  };
}
