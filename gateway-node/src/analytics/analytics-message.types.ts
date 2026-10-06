export const ANALYTICS_PROTOCOL_VERSION = 1 as const;

export const ANALYTICS_MESSAGE_TYPES = [
  "TRADE",
  "ANALYTICS_UPDATE",
  "RISK_EVENT",
] as const;

export type AnalyticsMessageType =
  (typeof ANALYTICS_MESSAGE_TYPES)[number];

export interface AnalyticsTradePayload {
  readonly tradeId: string;
  readonly symbol: string;
  readonly price: number;
  readonly quantity: number;
  readonly takerOrderId: string;
  readonly makerOrderId: string;
  readonly takerSide: "BUY" | "SELL";
  readonly buyOrderId: string;
  readonly sellOrderId: string;
}

export interface GatewayTradeMessage {
  readonly version: typeof ANALYTICS_PROTOCOL_VERSION;
  readonly type: "TRADE";
  readonly eventId: string;
  readonly requestId: string;
  readonly timestamp: string;
  readonly payload: AnalyticsTradePayload;
}

export interface AnalyticsUpdatePayload {
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
}

export interface GatewayAnalyticsUpdateMessage {
  readonly version: typeof ANALYTICS_PROTOCOL_VERSION;
  readonly type: "ANALYTICS_UPDATE";
  readonly eventId: string;
  readonly requestId: string;
  readonly timestamp: string;
  readonly payload: AnalyticsUpdatePayload;
}

export type RiskEventStatus = "warning" | "breached";

export interface AnalyticsRiskEventPayload {
  readonly eventId: string;
  readonly eventType: "RISK_LIMIT_WARNING" | "RISK_LIMIT_BREACHED";
  readonly symbol: string | null;
  readonly limitType: string;
  readonly status: RiskEventStatus;
  readonly threshold: number;
  readonly warningThreshold: number;
  readonly currentValue: number;
  readonly timestamp: string;
}

export interface GatewayRiskEventMessage {
  readonly version: typeof ANALYTICS_PROTOCOL_VERSION;
  readonly type: "RISK_EVENT";
  readonly eventId: string;
  readonly requestId: string;
  readonly timestamp: string;
  readonly payload: AnalyticsRiskEventPayload;
}

export type GatewayAnalyticsOutputMessage =
  | GatewayAnalyticsUpdateMessage
  | GatewayRiskEventMessage;
