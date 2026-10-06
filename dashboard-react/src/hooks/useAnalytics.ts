import { useCallback, useEffect, useMemo, useRef, useState } from "react";
import { createGatewayApiClient } from "../services/api";
import { createGatewayWebSocketClient, type GatewayWebSocketEvent } from "../services/websocket";
import type { GatewayWebSocketState } from "../types/websocket";
import type { AnalyticsPoint, AnalyticsSnapshot, RiskStatus } from "../types/analytics";

const MAX_ANALYTICS_POINTS = 120;

export interface AnalyticsHistoryPoint extends AnalyticsPoint {
  readonly eventId: string;
}

export interface AnalyticsData {
  readonly latest: AnalyticsSnapshot | null;
  readonly history: readonly AnalyticsHistoryPoint[];
  readonly state: "loading" | "ready" | "error";
  readonly error: string | null;
  readonly websocketState: GatewayWebSocketState;
  readonly refresh: () => Promise<void>;
}

function errorMessage(error: unknown): string {
  return error instanceof Error ? error.message : "Gateway request failed";
}

function isFiniteNumber(value: unknown): value is number {
  return typeof value === "number" && Number.isFinite(value);
}

function normalizeSnapshot(snapshot: AnalyticsSnapshot): AnalyticsHistoryPoint {
  return {
    ...snapshot,
    eventId: `snapshot-${snapshot.timestamp}`,
  };
}

function normalizeAnalyticsEvent(
  event: Extract<GatewayWebSocketEvent, { type: "ANALYTICS_UPDATE" }>,
  riskStatus: RiskStatus,
): AnalyticsHistoryPoint | null {
  const p = event.payload;
  const numericValues = [
    p.price, p.position, p.realizedPnl, p.unrealizedPnl,
    p.equity, p.peakEquity, p.drawdown,
  ];
  if (typeof p.symbol !== "string" || !numericValues.every(isFiniteNumber)) return null;
  if (p.vwap !== null && !isFiniteNumber(p.vwap)) return null;
  if (p.sma !== null && !isFiniteNumber(p.sma)) return null;
  if (p.ema !== null && !isFiniteNumber(p.ema)) return null;
  if (p.volatility !== null && !isFiniteNumber(p.volatility)) return null;

  return {
    symbol: p.symbol,
    price: p.price,
    vwap: p.vwap,
    sma: p.sma,
    ema: p.ema,
    volatility: p.volatility,
    position: p.position,
    realizedPnl: p.realizedPnl,
    unrealizedPnl: p.unrealizedPnl,
    equity: p.equity,
    peakEquity: p.peakEquity,
    drawdown: p.drawdown,
    riskStatus,
    timestamp: event.timestamp,
    eventId: event.eventId,
  };
}

export function useAnalytics(): AnalyticsData {
  const api = useMemo(() => createGatewayApiClient(), []);
  const [latest, setLatest] = useState<AnalyticsSnapshot | null>(null);
  const [history, setHistory] = useState<readonly AnalyticsHistoryPoint[]>([]);
  const [state, setState] = useState<AnalyticsData["state"]>("loading");
  const [error, setError] = useState<string | null>(null);
  const [websocketState, setWebsocketState] = useState<GatewayWebSocketState>("idle");
  const seenEventIds = useRef(new Set<string>());
  const riskStatus = useRef<RiskStatus>("ok");

  const refresh = useCallback(async (): Promise<void> => {
    setState("loading");
    setError(null);
    try {
      const snapshot = await api.getAnalytics();
      const point = normalizeSnapshot(snapshot);
      setLatest(snapshot);
      setHistory((current) => current.length === 0 ? [point] : current);
      setState("ready");
    } catch (reason) {
      setState("error");
      setError(errorMessage(reason));
    }
  }, [api]);

  useEffect(() => {
    let active = true;
    const client = createGatewayWebSocketClient({
      onStateChange: (nextState) => { if (active) setWebsocketState(nextState); },
      onEvent: (event) => {
        if (!active) return;

        if (event.type === "RISK_EVENT") {
          riskStatus.current = event.payload.status;
          setLatest((current) => current === null ? null : {
            ...current,
            riskStatus: riskStatus.current,
            timestamp: event.timestamp,
          });
          return;
        }

        if (event.type !== "ANALYTICS_UPDATE" || seenEventIds.current.has(event.eventId)) return;
        const point = normalizeAnalyticsEvent(event, riskStatus.current);
        if (point === null) {
          setError("Gateway sent an invalid analytics update");
          return;
        }

        seenEventIds.current.add(event.eventId);
        setLatest(point);
        setHistory((current) => [...current, point].slice(-MAX_ANALYTICS_POINTS));
        setState("ready");
        setError(null);
      },
    });

    void refresh();
    client.subscribe(["ANALYTICS_UPDATE", "RISK_EVENT"]);
    client.connect();

    return () => {
      active = false;
      client.disconnect();
    };
  }, [refresh]);

  return { latest, history, state, error, websocketState, refresh };
}
