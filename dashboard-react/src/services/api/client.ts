import type {
  AnalyticsSnapshot,
  ApiResponse,
  EngineStatus,
  GatewayStatus,
  MarketSnapshot,
  OrderBook,
  TradesResponse,
} from "../../types";

const DEFAULT_API_BASE_URL = "/api/v1";

function getApiBaseUrl(): string {
  const configuredUrl = import.meta.env.VITE_API_BASE_URL;

  return (configuredUrl ?? DEFAULT_API_BASE_URL).replace(/\/$/, "");
}

export class ApiError extends Error {
  readonly status: number;

  constructor(message: string, status: number) {
    super(message);
    this.name = "ApiError";
    this.status = status;
  }
}

async function request<T>(path: string): Promise<T> {
  const response = await fetch(`${getApiBaseUrl()}${path}`, {
    headers: {
      Accept: "application/json",
    },
  });

  if (!response.ok) {
    throw new ApiError(
      `Gateway request failed: ${response.status} ${response.statusText}`,
      response.status,
    );
  }

  const payload = (await response.json()) as ApiResponse<T>;

  return payload.data;
}

export const apiClient = {
  getStatus: (): Promise<GatewayStatus> =>
    request<GatewayStatus>("/status"),

  getEngineStatus: (): Promise<EngineStatus> =>
    request<EngineStatus>("/status/engine"),

  getMarket: (): Promise<MarketSnapshot> =>
    request<MarketSnapshot>("/market"),

  getOrderBook: (): Promise<OrderBook> =>
    request<OrderBook>("/orderbook"),

  getTrades: (): Promise<TradesResponse> =>
    request<TradesResponse>("/trades"),

  getAnalytics: (): Promise<AnalyticsSnapshot> =>
    request<AnalyticsSnapshot>("/analytics"),
};
