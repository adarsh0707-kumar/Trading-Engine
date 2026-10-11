import { useEffect, useMemo, useRef, useState } from "react";
import { createGatewayApiClient } from "../services/api";
import { createGatewayWebSocketClient, type GatewayWebSocketEvent } from "../services/websocket";
import { mergeRecentTrades } from "../services/tradeReconciliation";
import type { GatewayWebSocketState } from "../types/websocket";
import type { MarketSnapshot, Trade } from "../types";

const MAX_RECENT_TRADES = 25;
const MAX_SEEN_TRADE_IDS = 500;

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
  return { tradeId: event.eventId, symbol: event.payload.symbol, price: event.payload.price, quantity: event.payload.quantity, takerSide: event.payload.takerSide.toLowerCase(), timestamp: event.timestamp, buyOrderId: event.payload.buyOrderId, sellOrderId: event.payload.sellOrderId };
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
  const liveTradesById = useRef(new Map<string, Trade>());
  const hasMarketData = useRef(false);
  const hasTradeData = useRef(false);

  // Prevent an older REST response from overwriting newer WebSocket events or a
  // more recent manual refresh.
  const snapshotRequestId = useRef(0);
  const marketEventRevision = useRef(0);
  const tradeEventRevision = useRef(0);

  const rememberTradeIds = (ids: readonly string[]): void => {
    for (const id of ids) {
      seenTradeIds.current.delete(id);
      seenTradeIds.current.add(id);
    }
    while (seenTradeIds.current.size > MAX_SEEN_TRADE_IDS) {
      const oldest = seenTradeIds.current.values().next().value;
      if (oldest === undefined) break;
      seenTradeIds.current.delete(oldest);
    }
  };

  const rememberLiveTrade = (trade: Trade): void => {
    liveTradesById.current.delete(trade.tradeId);
    liveTradesById.current.set(trade.tradeId, trade);
    while (liveTradesById.current.size > MAX_RECENT_TRADES) {
      const oldest = liveTradesById.current.keys().next().value;
      if (oldest === undefined) break;
      liveTradesById.current.delete(oldest);
    }
    rememberTradeIds([trade.tradeId]);
  };

  const loadSnapshots = async (): Promise<void> => {
    const requestId = ++snapshotRequestId.current;
    const marketRevisionAtStart = marketEventRevision.current;
    const tradeRevisionAtStart = tradeEventRevision.current;

    setMarketState((current) => hasMarketData.current ? current : "loading");
    setTradesState((current) => hasTradeData.current ? current : "loading");
    setMarketError(null);
    setTradesError(null);
    const [marketResult, tradesResult] = await Promise.allSettled([api.getMarket(), api.getTrades()]);

    // A later refresh owns the result now; don't let this request race it.
    if (requestId !== snapshotRequestId.current) return;

    if (marketResult.status === "fulfilled") {
      if (marketRevisionAtStart === marketEventRevision.current) {
        hasMarketData.current = true;
        setMarket(marketResult.value);
        setMarketState("ready");
        setMarketError(null);
      }
    } else if (marketRevisionAtStart === marketEventRevision.current) {
      setMarketState(hasMarketData.current ? "ready" : "error");
      setMarketError(errorMessage(marketResult.reason));
    }

    if (tradesResult.status === "fulfilled") {
      if (tradeRevisionAtStart === tradeEventRevision.current) {
        const nextTrades = mergeRecentTrades(
          tradesResult.value.trades,
          [...liveTradesById.current.values()],
          MAX_RECENT_TRADES,
        );
        hasTradeData.current = nextTrades.length > 0 || hasTradeData.current;
        rememberTradeIds(nextTrades.map((trade) => trade.tradeId));
        setTrades(nextTrades);
        setTradesState("ready");
        setTradesError(null);
      }
    } else if (tradeRevisionAtStart === tradeEventRevision.current) {
      setTradesState(hasTradeData.current ? "ready" : "error");
      setTradesError(errorMessage(tradesResult.reason));
    }
  };

  useEffect(() => {
    let active = true;
    const client = createGatewayWebSocketClient({
      onStateChange: (state) => { if (active) setWebsocketState(state); },
      onEvent: (event) => {
        if (!active) return;

        if (event.type === "MARKET_DATA") {
          marketEventRevision.current += 1;
          hasMarketData.current = true;
          setMarket((current) => ({
            symbol: event.payload.symbol,
            lastPrice: event.payload.price,
            lastQuantity: current?.lastQuantity ?? 0,
            timestamp: event.timestamp,
          }));
          setMarketState("ready");
          setMarketError(null);
          return;
        }

        if (event.type !== "TRADE") return;
        tradeEventRevision.current += 1;
        marketEventRevision.current += 1;
        const trade = tradeFromEvent(event);
        if (seenTradeIds.current.has(trade.tradeId)) return;
        rememberLiveTrade(trade);
        hasTradeData.current = true;
        hasMarketData.current = true;
        setTrades((current) => [trade, ...current].slice(0, MAX_RECENT_TRADES));
        setTradesState("ready");
        setTradesError(null);
        setMarket({ symbol: trade.symbol, lastPrice: trade.price, lastQuantity: trade.quantity, timestamp: trade.timestamp });
        setMarketState("ready");
        setMarketError(null);
      },
    });
    void loadSnapshots();
    client.subscribe(["TRADE", "MARKET_DATA"]);
    client.connect();
    return () => { active = false; client.disconnect(); };
  }, [api]);

  return { market, trades, marketState, tradesState, marketError, tradesError, websocketState, refresh: loadSnapshots };
}
