import { useEffect, useMemo, useRef, useState } from "react";
import { createGatewayApiClient } from "../services/api";
import {
  createGatewayWebSocketClient,
  type GatewayWebSocketEvent,
  type GatewayWebSocketState,
} from "../services/websocket";
import type { MarketSnapshot, Trade } from "../types";

const MAX_RECENT_TRADES = 25;

export interface LiveTradingData {
  readonly market: MarketSnapshot | null;
  readonly trades: readonly Trade[];
  readonly marketState: "loading" | "ready" | "error";
  readonly tradesState: "loading" | "ready" | "error";
  readonly marketError: string | null;
  readonly tradesError: string | null;
  readonly websocketState: GatewayWebSocketState;
  readonly refresh: () => Promise<void>;
}

function errorMessage(error: unknown): string {
  return error instanceof Error ? error.message : "Gateway request failed";
}

function tradeFromEvent(event: Extract<GatewayWebSocketEvent, { type: "TRADE" }>): Trade {
  return {
    tradeId: event.eventId,
    symbol: event.payload.symbol,
    price: event.payload.price,
    quantity: event.payload.quantity,
    takerSide: event.payload.takerSide.toLowerCase(),
    timestamp: event.timestamp,
    buyOrderId: event.payload.buyOrderId,
    sellOrderId: event.payload.sellOrderId,
  };
}

export function useLiveTradingData(): LiveTradingData {
  const api = useMemo(() => createGatewayApiClient(), []);
  const [market, setMarket] = useState<MarketSnapshot | null>(null);
  const [trades, setTrades] = useState<readonly Trade[]>([]);
  const [marketState, setMarketState] = useState<LiveTradingData["marketState"]>("loading");
  const [tradesState, setTradesState] = useState<LiveTradingData["tradesState"]>("loading");
  const [marketError, setMarketError] = useState<string | null>(null);
  const [tradesError, setTradesError] = useState<string | null>(null);
  const [websocketState, setWebsocketState] = useState<GatewayWebSocketState>("idle");
  const seenTradeIds = useRef(new Set<string>());

  const loadSnapshots = async (): Promise<void> => {
    setMarketState("loading");
    setTradesState("loading");
    setMarketError(null);
    setTradesError(null);

    const [marketResult, tradesResult] = await Promise.allSettled([
      api.getMarket(),
      api.getTrades(),
    ]);

    if (marketResult.status === "fulfilled") {
      setMarket(marketResult.value);
      setMarketState("ready");
    } else {
      setMarketState("error");
      setMarketError(errorMessage(marketResult.reason));
    }

    if (tradesResult.status === "fulfilled") {
      const nextTrades = tradesResult.value.trades.slice(0, MAX_RECENT_TRADES);
      seenTradeIds.current = new Set(nextTrades.map((trade) => trade.tradeId));
      setTrades(nextTrades);
      setTradesState("ready");
    } else {
      setTradesState("error");
      setTradesError(errorMessage(tradesResult.reason));
    }
  };

  useEffect(() => {
    let active = true;

    const client = createGatewayWebSocketClient({
      onStateChange: (state) => {
        if (active) setWebsocketState(state);
      },
      onEvent: (event) => {
        if (!active || event.type !== "TRADE") return;

        const trade = tradeFromEvent(event);
        if (seenTradeIds.current.has(trade.tradeId)) return;

        seenTradeIds.current.add(trade.tradeId);
        setTrades((current) => [trade, ...current].slice(0, MAX_RECENT_TRADES));
        setTradesState("ready");
        setTradesError(null);
        setMarket({
          symbol: trade.symbol,
          lastPrice: trade.price,
          lastQuantity: trade.quantity,
          timestamp: trade.timestamp,
        });
        setMarketState("ready");
        setMarketError(null);
      },
    });

    void loadSnapshots();
    client.subscribe(["TRADE"]);
    client.connect();

    return () => {
      active = false;
      client.disconnect();
    };
  }, [api]);

  return {
    market,
    trades,
    marketState,
    tradesState,
    marketError,
    tradesError,
    websocketState,
    refresh: loadSnapshots,
  };
}
