import type { WebSocket } from "ws";

import type {
  GatewayWebSocketEvent,
  WebSocketClientMessage,
  WebSocketConnection,
  WebSocketEventType,
} from "./websocket.types.ts";
import { WEBSOCKET_EVENT_TYPES } from "./websocket.types.ts";

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
    throw new Error("WebSocket message must contain valid JSON");
  }

  if (typeof value !== "object" || value === null) {
    throw new Error("WebSocket message must be a JSON object");
  }

  const record = value as Record<string, unknown>;

  if (record.action !== "subscribe" && record.action !== "unsubscribe") {
    throw new Error("WebSocket action must be subscribe or unsubscribe");
  }

  if (!Array.isArray(record.events) || record.events.length === 0) {
    throw new Error("WebSocket events must be a non-empty array");
  }

  const events = record.events.filter(isEventType);

  if (events.length !== record.events.length) {
    throw new Error("WebSocket message contains an unsupported event type");
  }

  return {
    action: record.action,
    events,
  } as WebSocketClientMessage;
}

function serializeEvent(event: GatewayWebSocketEvent): string {
  return JSON.stringify({
    type: event.type,
    eventId: event.eventId,
    timestamp: event.timestamp,
    payload: event.payload,
  });
}

function serializeError(message: string): string {
  return JSON.stringify({
    type: "ERROR",
    error: {
      code: "INVALID_CLIENT_MESSAGE",
      message,
    },
  });
}

export function createWebSocketHub(
  options: WebSocketHubOptions,
): WebSocketHub {
  const clients = new Set<WebSocketConnection>();

  const remove = (client: WebSocketConnection): void => {
    clients.delete(client);
    client.queue.length = 0;
  };

  const flush = (client: WebSocketConnection): void => {
    if (client.flushing || client.socket.readyState !== OPEN) {
      return;
    }

    const next = client.queue.shift();

    if (next === undefined) {
      return;
    }

    client.flushing = true;

    try {
      client.socket.send(next, (error?: Error) => {
        client.flushing = false;

        if (error !== undefined) {
          remove(client);
          client.socket.terminate();
          return;
        }

        flush(client);
      });
    } catch {
      client.flushing = false;
      remove(client);
      client.socket.terminate();
    }
  };

  const enqueue = (
    client: WebSocketConnection,
    message: string,
  ): void => {
    if (client.socket.readyState !== OPEN) {
      return;
    }

    if (client.queue.length >= options.maxQueueSize) {
      remove(client);
      client.socket.close(1013, "WebSocket client queue is full");
      return;
    }

    client.queue.push(message);
    flush(client);
  };

  const add = (socket: WebSocket): void => {
    const client: WebSocketConnection = {
      socket,
      subscriptions: new Set<WebSocketEventType>(),
      queue: [],
      flushing: false,
      alive: true,
    };

    clients.add(client);

    socket.on("message", (data) => {
      try {
        const message = parseClientMessage(data.toString());

        for (const eventType of message.events) {
          if (message.action === "subscribe") {
            client.subscriptions.add(eventType);
          } else {
            client.subscriptions.delete(eventType);
          }
        }

        enqueue(
          client,
          JSON.stringify({
            type: "SUBSCRIPTION_UPDATED",
            subscriptions: [...client.subscriptions],
          }),
        );
      } catch (error) {
        const message =
          error instanceof Error
            ? error.message
            : "Invalid WebSocket client message";

        enqueue(client, serializeError(message));
      }
    });

    socket.on("pong", () => {
      client.alive = true;
    });

    socket.on("close", () => {
      remove(client);
    });

    socket.on("error", () => {
      remove(client);
    });

    enqueue(
      client,
      JSON.stringify({
        type: "CONNECTION_READY",
        subscriptions: [],
      }),
    );
  };

  const publish = (event: GatewayWebSocketEvent): void => {
    for (const client of clients) {
      if (!client.subscriptions.has(event.type)) {
        continue;
      }

      enqueue(client, serializeEvent(event));
    }
  };

  let heartbeatTimer: ReturnType<typeof setInterval> | undefined;

  const startHeartbeat = (): void => {
    if (heartbeatTimer !== undefined) {
      return;
    }

    heartbeatTimer = setInterval(() => {
      for (const client of clients) {
        if (client.socket.readyState !== OPEN) {
          remove(client);
          continue;
        }

        if (!client.alive) {
          remove(client);
          client.socket.terminate();
          continue;
        }

        client.alive = false;
        client.socket.ping();
      }
    }, options.heartbeatIntervalMs);
  };

  const stopHeartbeat = (): void => {
    if (heartbeatTimer === undefined) {
      return;
    }

    clearInterval(heartbeatTimer);
    heartbeatTimer = undefined;
  };

  const closeAll = (
    code = 1001,
    reason = "Gateway is shutting down",
  ): void => {
    for (const client of clients) {
      remove(client);

      if (client.socket.readyState === OPEN) {
        client.socket.close(code, reason);
      }
    }
  };

  return {
    add,
    publish,
    closeAll,
    size: () => clients.size,
    startHeartbeat,
    stopHeartbeat,
  };
}
