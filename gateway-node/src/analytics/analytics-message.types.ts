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
