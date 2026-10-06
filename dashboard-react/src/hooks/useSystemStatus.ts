import { useCallback, useEffect, useMemo, useState } from "react";
import { createGatewayApiClient } from "../services/api";
import type { EngineStatus, GatewayStatus } from "../types/system";

const POLL_INTERVAL_MS = 5_000;

export interface SystemStatusData {
  readonly gateway: GatewayStatus | null;
  readonly engine: EngineStatus | null;
  readonly state: "loading" | "ready" | "error";
  readonly error: string | null;
  readonly refreshedAt: number | null;
  readonly refresh: () => Promise<void>;
}

function errorMessage(error: unknown): string {
  return error instanceof Error ? error.message : "Gateway request failed";
}

export function useSystemStatus(): SystemStatusData {
  const api = useMemo(() => createGatewayApiClient(), []);
  const [gateway, setGateway] = useState<GatewayStatus | null>(null);
  const [engine, setEngine] = useState<EngineStatus | null>(null);
  const [state, setState] = useState<SystemStatusData["state"]>("loading");
  const [error, setError] = useState<string | null>(null);
  const [refreshedAt, setRefreshedAt] = useState<number | null>(null);

  const refresh = useCallback(async (): Promise<void> => {
    try {
      const [nextGateway, nextEngine] = await Promise.all([
        api.getStatus(),
        api.getEngineStatus(),
      ]);
      setGateway(nextGateway);
      setEngine(nextEngine);
      setState("ready");
      setError(null);
      setRefreshedAt(Date.now());
    } catch (reason) {
      setState((current) => current === "ready" ? current : "error");
      setError(errorMessage(reason));
    }
  }, [api]);

  useEffect(() => {
    let active = true;

    const poll = async (): Promise<void> => {
      if (!active) return;
      await refresh();
    };

    void poll();
    const timer = globalThis.setInterval(() => {
      void poll();
    }, POLL_INTERVAL_MS);

    return () => {
      active = false;
      globalThis.clearInterval(timer);
    };
  }, [refresh]);

  return { gateway, engine, state, error, refreshedAt, refresh };
}
