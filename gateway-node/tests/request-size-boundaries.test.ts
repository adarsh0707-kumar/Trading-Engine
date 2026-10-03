import { describe, expect, test } from "bun:test";

import { loadConfig } from "../src/config/config.ts";
import { createGatewayServer } from "../src/server.ts";
import { createWebSocketHub } from "../src/websocket/websocket-hub.ts";

function createSocket() {
  const listeners = new Map<string, (...args: any[]) => void>();
  const closed: Array<{ code: number; reason: string }> = [];

  return {
    readyState: 1,
    closed,
    on(event: string, listener: (...args: any[]) => void) {
      listeners.set(event, listener);
    },
    send(_message: string, callback?: (error?: Error) => void) {
      callback?.();
    },
    close(code?: number, reason?: string) {
      closed.push({ code: code ?? 1000, reason: reason ?? "" });
    },
    terminate() {},
    emit(event: string, ...args: any[]) {
      listeners.get(event)?.(...args);
    },
  } as any;
}

describe("request size boundaries", () => {
  test("keeps HTTP and WebSocket payload limits at or below 1 MiB", () => {
    const config = loadConfig({});

    expect(config.http.bodyLimitBytes).toBe(1024 * 1024);
    expect(config.websocket.maxPayloadBytes).toBe(1024 * 1024);
  });

  test("allows smaller configured HTTP and WebSocket payload limits", () => {
    const config = loadConfig({
      HTTP_BODY_LIMIT_BYTES: "65536",
      WEBSOCKET_MAX_PAYLOAD_BYTES: "32768",
    });

    expect(config.http.bodyLimitBytes).toBe(65536);
    expect(config.websocket.maxPayloadBytes).toBe(32768);
  });

  test("rejects transport payload limits above 1 MiB", () => {
    expect(() =>
      loadConfig({
        HTTP_BODY_LIMIT_BYTES: String(1024 * 1024 + 1),
      }),
    ).toThrow("HTTP_BODY_LIMIT_BYTES must be at most 1048576");

    expect(() =>
      loadConfig({
        WEBSOCKET_MAX_PAYLOAD_BYTES: String(1024 * 1024 + 1),
      }),
    ).toThrow("WEBSOCKET_MAX_PAYLOAD_BYTES must be at most 1048576");
  });

  test("closes an oversized WebSocket message with status 1009", () => {
    const socket = createSocket();
    const hub = createWebSocketHub({
      maxQueueSize: 8,
      heartbeatIntervalMs: 30_000,
      maxMessageBytes: 16,
    });

    hub.add(socket);

    socket.emit(
      "message",
      JSON.stringify({
        action: "subscribe",
        events: ["TRADE"],
        padding: "x".repeat(32),
      }),
    );

    expect(socket.closed).toEqual([
      {
        code: 1009,
        reason: "WebSocket message exceeds the maximum size of 16 bytes",
      },
    ]);
    expect(hub.size()).toBe(0);
  });

  test("returns HTTP 413 when the configured body limit is exceeded", async () => {
    const gateway = createGatewayServer({
      HTTP_BODY_LIMIT_BYTES: "64",
      ENGINE_CONNECT_TIMEOUT_MS: "1000",
      ANALYTICS_CONNECT_TIMEOUT_MS: "1000",
    });

    const response = await gateway.app.inject({
      method: "POST",
      url: "/api/v1/engine/start",
      headers: {
        "content-type": "application/json",
      },
      payload: JSON.stringify({
        padding: "x".repeat(128),
      }),
    });

    expect(response.statusCode).toBe(413);
    expect(response.json() as {
      readonly error: {
        readonly code: string;
        readonly message: string;
        readonly request_id: string;
      };
    }).toEqual({
      error: {
        code: "INVALID_ARGUMENT",
        message: "Request payload exceeds the configured maximum size",
        request_id: expect.any(String),
      },
    });

    await gateway.stop();
  });
});
