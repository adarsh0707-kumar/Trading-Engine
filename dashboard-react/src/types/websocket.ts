export const GATEWAY_WEBSOCKET_EVENT_TYPES = [
  "TRADE",
  "ANALYTICS_UPDATE",
  "RISK_EVENT",
] as const;

export type GatewayWebSocketEventType =
  (typeof GATEWAY_WEBSOCKET_EVENT_TYPES)[number];

export interface GatewayTradeWebSocketEvent {
  readonly type: "TRADE";
  readonly eventId: string;
  readonly requestId: string;
  readonly timestamp: string;
  readonly payload: {
    readonly symbol: string;
    readonly price: number;
    readonly quantity: number;
    readonly takerOrderId: string;
    readonly makerOrderId: string;
    readonly takerSide: "BUY" | "SELL";
    readonly buyOrderId: string;
    readonly sellOrderId: string;
  };
}

export interface GatewayAnalyticsUpdateWebSocketEvent {
  readonly type: "ANALYTICS_UPDATE";
  readonly eventId: string;
  readonly requestId: string;
  readonly timestamp: string;
  readonly payload: {
    readonly symbol: string;
    readonly price: number;
    readonly vwap: number | null;
    readonly sma: number | null;
    readonly ema: number | null;
    readonly volatility: number | null;
    readonly position: number;
    readonly realizedPnl: number;
    readonly unrealizedPnl: number;
    readonly equity: number;
    readonly peakEquity: number;
    readonly drawdown: number;
  };
}

export interface GatewayRiskEventWebSocketEvent {
  readonly type: "RISK_EVENT";
  readonly eventId: string;
  readonly requestId: string;
  readonly timestamp: string;
  readonly payload: {
    readonly eventId: string;
    readonly eventType: "RISK_LIMIT_WARNING" | "RISK_LIMIT_BREACHED";
    readonly symbol: string | null;
    readonly limitType: string;
    readonly status: "warning" | "breached";
    readonly threshold: number;
    readonly warningThreshold: number;
    readonly currentValue: number;
    readonly timestamp: string;
  };
}

export type GatewayWebSocketEvent =
  | GatewayTradeWebSocketEvent
  | GatewayAnalyticsUpdateWebSocketEvent
  | GatewayRiskEventWebSocketEvent;

export type GatewayWebSocketState =
  | "idle"
  | "connecting"
  | "open"
  | "reconnecting"
  | "closed";

export interface GatewayWebSocketError {
  readonly code: string;
  readonly message: string;
}

export interface GatewayWebSocket {
  readonly readyState: number;
  onopen: (() => void) | null;
  onmessage: ((event: { data: unknown }) => void) | null;
  onerror: (() => void) | null;
  onclose: (() => void) | null;
  send(data: string): void;
  close(): void;
}

export interface GatewayWebSocketOptions {
  readonly baseUrl?: string;
  readonly path?: string;
  readonly reconnect?: boolean;
  readonly maxReconnectAttempts?: number;
  readonly reconnectInitialDelayMs?: number;
  readonly reconnectMaxDelayMs?: number;
  readonly webSocketFactory?: (url: string) => GatewayWebSocket;
  readonly onStateChange?: (state: GatewayWebSocketState) => void;
  readonly onEvent?: (event: GatewayWebSocketEvent) => void;
  readonly onError?: (error: GatewayWebSocketError) => void;
}

export interface GatewayWebSocketClient {
  readonly connect: () => void;
  readonly disconnect: () => void;
  readonly subscribe: (
    events: readonly GatewayWebSocketEventType[],
  ) => void;
  readonly unsubscribe: (
    events: readonly GatewayWebSocketEventType[],
  ) => void;
  readonly getState: () => GatewayWebSocketState;
}
