import type { WebSocket } from "ws";

import type { NormalizedEngineEventResult } from "../engine-protocol/engine-event.ts";
import type {
  AnalyticsUpdatePayload,
  AnalyticsRiskEventPayload,
} from "../analytics/analytics-message.types.ts";

export const WEBSOCKET_EVENT_TYPES = [
  "TRADE",
  "ANALYTICS_UPDATE",
  "RISK_EVENT",
] as const;

export type WebSocketEventType = (typeof WEBSOCKET_EVENT_TYPES)[number];

export interface WebSocketSubscribeMessage {
  readonly action: "subscribe";
  readonly events: readonly WebSocketEventType[];
}

export interface WebSocketUnsubscribeMessage {
  readonly action: "unsubscribe";
  readonly events: readonly WebSocketEventType[];
}

export type WebSocketClientMessage =
  | WebSocketSubscribeMessage
  | WebSocketUnsubscribeMessage;

export interface WebSocketConnection {
  readonly socket: WebSocket;
  readonly subscriptions: Set<WebSocketEventType>;
  readonly queue: string[];
  flushing: boolean;
  alive: boolean;
}

export interface GatewayAnalyticsUpdateWebSocketEvent {
  readonly type: "ANALYTICS_UPDATE";
  readonly eventId: string;
  readonly timestamp: string;
  readonly payload: AnalyticsUpdatePayload;
}

export interface GatewayRiskEventWebSocketEvent {
  readonly type: "RISK_EVENT";
  readonly eventId: string;
  readonly timestamp: string;
  readonly payload: AnalyticsRiskEventPayload;
}

export type GatewayWebSocketEvent =
  | NormalizedEngineEventResult
  | GatewayAnalyticsUpdateWebSocketEvent
  | GatewayRiskEventWebSocketEvent;
