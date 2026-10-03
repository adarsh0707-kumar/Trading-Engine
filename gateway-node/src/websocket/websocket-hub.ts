import type { WebSocket } from "ws";

import type {
  GatewayWebSocketEvent,
  WebSocketClientMessage,
  WebSocketConnection,
  WebSocketEventType,
} from "./websocket.types.ts";
import { WEBSOCKET_EVENT_TYPES } from "./websocket.types.ts";
import {
  assertExactKeys,
  isRecord,
  validateUniqueStringArray,
} from "../security/input-validation.ts";

export interface WebSocketHubOptions {
  readonly maxQueueSize: number;
  readonly heartbeatIntervalMs: number;
}

export interface WebSocketHub {
  readonly add: (socket: WebSocket) => void;
  readonly publish: (event: GatewayWebSocketEvent) => void;
  readonly closeAll: (code?: number, reason?: string) => void;
  readonly size: () => number;
  readonly startHeartbeat: () => void;
  readonly stopHeartbeat: () => void;
}

const OPEN = 1;

function isEventType(value: unknown): value is WebSocketEventType {
  return (
    typeof value === "string" &&
    (WEBSOCKET_EVENT_TYPES as readonly string[]).includes(value)
  );
}

function parseClientMessage(raw: string): WebSocketClientMessage {
  let value: unknown;

  try {
    value = JSON.parse(raw);
  } catch {
    throw new Error("WebSocket message contains invalid JSON");
  }

  if (!isRecord(value)) {
    throw new Error("WebSocket message must be a JSON object");
  }

  assertExactKeys(
    value,
    ["action", "events"],
    "WebSocket message",
  );

  if (value.action !== "subscribe" && value.action !== "unsubscribe") {
    throw new Error("WebSocket action must be subscribe or unsubscribe");
  }

  const eventValues = validateUniqueStringArray(
    value.events,
    "WebSocket events",
    WEBSOCKET_EVENT_TYPES.length,
  );

  const events = eventValues.filter(isEventType);

  if (events.length !== eventValues.length) {
    throw new Error("WebSocket message contains an unsupported event type");
  }

  return {
    action: value.action,
    events,
  } as WebSocketClientMessage;
}

