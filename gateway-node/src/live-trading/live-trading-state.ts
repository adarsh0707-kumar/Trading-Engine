import type { NormalizedTradeEvent } from "../engine-protocol/engine-trade.types.ts";
import type { NormalizedMarketDataEvent } from "../engine-protocol/engine-market-data.types.ts";
import type {
  MarketProvider,
  MarketState,
} from "../market/market.types.ts";
import type {
  Trade,
  TradesProvider,
  TradesState,
} from "../trades/trades.types.ts";

const DEFAULT_MAX_TRADES = 100;

export interface LiveTradingState
  extends MarketProvider, TradesProvider {
  readonly onTrade: (event: NormalizedTradeEvent) => void;
  readonly onMarketData: (event: NormalizedMarketDataEvent) => void;
}

export function createLiveTradingState(
  maxTrades = DEFAULT_MAX_TRADES,
): LiveTradingState {
  if (!Number.isInteger(maxTrades) || maxTrades <= 0) {
    throw new Error("maxTrades must be a positive integer");
  }

  let market: MarketState | null = null;
  let trades: Trade[] = [];
  const seenTradeIds = new Set<string>();

  return {
    onMarketData(event: NormalizedMarketDataEvent): void {
      market = {
        symbol: event.payload.symbol,
        lastPrice: event.payload.price,
        // This field represents the last executed trade quantity, not tick size.
        lastQuantity: market?.lastQuantity ?? 0,
        timestamp: event.timestamp,
      };
    },

    onTrade(event: NormalizedTradeEvent): void {
      const { payload } = event;
      if (seenTradeIds.has(event.tradeId)) return;
      seenTradeIds.add(event.tradeId);

      if (
        market === null ||
        Date.parse(event.timestamp) >= Date.parse(market.timestamp)
      ) {
        market = {
          symbol: payload.symbol,
          lastPrice: payload.price,
          lastQuantity: payload.quantity,
          timestamp: event.timestamp,
        };
      }

      const trade: Trade = {
        tradeId: event.tradeId,
        symbol: payload.symbol,
        price: payload.price,
        quantity: payload.quantity,
        takerSide: payload.takerSide.toLowerCase() as "buy" | "sell",
        timestamp: event.timestamp,
      };

      trades = [trade, ...trades]
        .sort((left, right) => Date.parse(right.timestamp) - Date.parse(left.timestamp))
        .slice(0, maxTrades);
    },

    getMarket(): MarketState | null {
      return market;
    },

    getTrades(): TradesState {
      return {
        trades: [...trades],
      };
    },
  };
}
