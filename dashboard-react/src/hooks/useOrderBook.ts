import { useCallback, useEffect, useMemo, useState } from "react";
import { createGatewayApiClient } from "../services/api";
import type { OrderBook } from "../types";

export type OrderBookState = "loading" | "ready" | "error";

function errorMessage(error: unknown): string {
  return error instanceof Error ? error.message : "Gateway request failed";
}

export interface UseOrderBookResult {
  readonly orderBook: OrderBook | null;
  readonly state: OrderBookState;
  readonly error: string | null;
  readonly refresh: () => Promise<void>;
}

export function useOrderBook(): UseOrderBookResult {
  const api = useMemo(() => createGatewayApiClient(), []);
  const [orderBook, setOrderBook] = useState<OrderBook | null>(null);
  const [state, setState] = useState<OrderBookState>("loading");
  const [error, setError] = useState<string | null>(null);

  const refresh = useCallback(async (): Promise<void> => {
    setState("loading");
    setError(null);

    try {
      const snapshot = await api.getOrderBook();
      setOrderBook(snapshot);
      setState("ready");
    } catch (reason) {
      setState("error");
      setError(errorMessage(reason));
    }
  }, [api]);

  useEffect(() => {
    void refresh();
  }, [refresh]);

  return { orderBook, state, error, refresh };
}
