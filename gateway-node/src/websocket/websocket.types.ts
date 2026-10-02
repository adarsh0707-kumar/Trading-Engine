import type { WebSocket } from "ws";

import type { NormalizedEngineEventResult } from "../engine-protocol/engine-event.ts";

export const WEBSOCKET_EVENT_TYPES = ["TRADE"] as const;

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

export type GatewayWebSocketEvent = NormalizedEngineEventResult;
