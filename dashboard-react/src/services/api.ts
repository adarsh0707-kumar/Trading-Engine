import type {
  AnalyticsSnapshot,
  ApiResponse,
  EngineStatus,
  GatewayStatus,
  MarketSnapshot,
  OrderBook,
  TradesResponse,
} from "../types";

export interface GatewayApiErrorBody {
  error?: { code?: string; message?: string; request_id?: string };
}

export class GatewayApiError extends Error {
  readonly code: string;
  readonly requestId: string | null;
  readonly status: number;

  constructor(message: string, options: { code?: string; requestId?: string | null; status: number }) {
    super(message);
    this.name = "GatewayApiError";
    this.code = options.code ?? "HTTP_ERROR";
    this.requestId = options.requestId ?? null;
    this.status = options.status;
  }
}

type GatewayFetch = (
  input: RequestInfo | URL,
  init?: RequestInit,
) => Promise<Response>;

export interface GatewayApiClientOptions {
  readonly baseUrl?: string;
  readonly timeoutMs?: number;
  readonly fetch?: GatewayFetch;
}

const DEFAULT_BASE_URL = "";
const DEFAULT_TIMEOUT_MS = 5_000;

function resolveBaseUrl(baseUrl: string | undefined): string {
  const configured = baseUrl ?? import.meta.env.VITE_GATEWAY_BASE_URL ?? DEFAULT_BASE_URL;
  return configured.replace(/\/+$/, "");
}

function createTimeoutSignal(timeoutMs: number): { signal: AbortSignal; cleanup: () => void } {
  const controller = new AbortController();
  const timer = globalThis.setTimeout(() => controller.abort(), timeoutMs);
  return { signal: controller.signal, cleanup: () => globalThis.clearTimeout(timer) };
}

async function parseErrorBody(response: Response): Promise<GatewayApiErrorBody> {
  try {
    const body: unknown = await response.json();
    if (typeof body === "object" && body !== null) return body as GatewayApiErrorBody;
  } catch {
    // The response is not JSON; the HTTP status still provides useful context.
  }
  return {};
}

export function createGatewayApiClient(options: GatewayApiClientOptions = {}) {
  const baseUrl = resolveBaseUrl(options.baseUrl);
  const timeoutMs = options.timeoutMs ?? DEFAULT_TIMEOUT_MS;
  const requestFetch = options.fetch ?? globalThis.fetch;

  async function get<T>(path: string): Promise<T> {
    const timeout = createTimeoutSignal(timeoutMs);
    const url = `${baseUrl}${path}`;
    try {
      const response = await requestFetch(url, {
        method: "GET",
        headers: { Accept: "application/json" },
        signal: timeout.signal,
      });
      if (!response.ok) {
        const body = await parseErrorBody(response);
        throw new GatewayApiError(
          body.error?.message ?? `Gateway request failed with status ${response.status}`,
          { code: body.error?.code, requestId: body.error?.request_id, status: response.status },
        );
      }
      const body: unknown = await response.json();
      if (typeof body !== "object" || body === null || !("data" in body)) {
        throw new GatewayApiError("Gateway response is missing the data envelope", {
          code: "INVALID_RESPONSE", status: response.status,
        });
      }
      return (body as ApiResponse<T>).data;
    } catch (error) {
      if (error instanceof GatewayApiError) throw error;
      if (error instanceof DOMException && error.name === "AbortError") {
        throw new GatewayApiError(`Gateway request timed out after ${timeoutMs}ms`, { code: "TIMEOUT", status: 0 });
      }
      throw new GatewayApiError(error instanceof Error ? error.message : "Gateway request failed", {
        code: "NETWORK_ERROR", status: 0,
      });
    } finally {
      timeout.cleanup();
    }
  }

  return {
    getStatus: () => get<GatewayStatus>("/api/v1/status"),
    getEngineStatus: () => get<EngineStatus>("/api/v1/status/engine"),
    getMarket: () => get<MarketSnapshot>("/api/v1/market"),
    getOrderBook: () => get<OrderBook>("/api/v1/orderbook"),
    getTrades: () => get<TradesResponse>("/api/v1/trades"),
    getAnalytics: () => get<AnalyticsSnapshot>("/api/v1/analytics"),
  };
}

export type GatewayApiClient = ReturnType<typeof createGatewayApiClient>;
export const gatewayApi = createGatewayApiClient();