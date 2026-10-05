import type { NormalizedTradeEvent } from "../engine-protocol/engine-trade.types.ts";
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
}

export function createLiveTradingState(
  maxTrades = DEFAULT_MAX_TRADES,
): LiveTradingState {
  if (!Number.isInteger(maxTrades) || maxTrades <= 0) {
    throw new Error("maxTrades must be a positive integer");
  }

  let market: MarketState | null = null;
  let trades: Trade[] = [];

  return {
    onTrade(event: NormalizedTradeEvent): void {
      const { payload } = event;

      market = {
        symbol: payload.symbol,
        lastPrice: payload.price,
        lastQuantity: payload.quantity,
        timestamp: event.timestamp,
      };

      const trade: Trade = {
        tradeId: event.tradeId,
        symbol: payload.symbol,
        price: payload.price,
        quantity: payload.quantity,
        takerSide: payload.takerSide.toLowerCase() as "buy" | "sell",
        timestamp: event.timestamp,
      };

      trades = [trade, ...trades].slice(0, maxTrades);
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
