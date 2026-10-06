import { describe, expect, test } from "bun:test";

import { createWebSocketHub } from "../src/websocket/websocket-hub.ts";

function createSocket() {
  const listeners = new Map<string, (...args: any[]) => void>();
  const sent: string[] = [];

  return {
    readyState: 1,
    sent,
    on(event: string, listener: (...args: any[]) => void) {
      listeners.set(event, listener);
    },
    send(message: string, callback?: (error?: Error) => void) {
      sent.push(message);
      callback?.();
    },
    close() {},
    terminate() {},
    emit(event: string, ...args: any[]) {
      listeners.get(event)?.(...args);
    },
  } as any;
}

const trade = {
  type: "TRADE" as const,
  eventId: "event-1",
  tradeId: "trade-1",
  requestId: "request-1",
  timestamp: "2026-10-02T12:00:00.000Z",
  payload: {
    symbol: "BTC-USD",
    price: 100,
    quantity: 2,
    takerOrderId: "order-1",
    makerOrderId: "order-2",
    takerSide: "BUY" as const,
    buyOrderId: "order-1",
    sellOrderId: "order-2",
  },
};

const analyticsUpdate = {
  type: "ANALYTICS_UPDATE" as const,
  eventId: "analytics-event-1",
  requestId: "trade-request-1",
  timestamp: "2026-10-02T12:00:01.000Z",
  payload: {
    symbol: "BTC-USD",
    price: 100,
    vwap: null,
    sma: null,
    ema: null,
    volatility: null,
    position: 2,
    realizedPnl: 0,
    unrealizedPnl: 0.5,
    equity: 1000.5,
    peakEquity: 1000.5,
    drawdown: 0,
  },
};

describe("websocket hub", () => {
  test("registers clients and sends the connection-ready message", () => {
    const socket = createSocket();
    const hub = createWebSocketHub({ maxQueueSize: 8, heartbeatIntervalMs: 30_000 });

    hub.add(socket);

    expect(hub.size()).toBe(1);
    expect(JSON.parse(socket.sent[0])).toEqual({
      type: "CONNECTION_READY",
      subscriptions: [],
    });
  });

  test("updates subscriptions and publishes matching events with correlation fields", () => {
    const socket = createSocket();
    const hub = createWebSocketHub({ maxQueueSize: 8, heartbeatIntervalMs: 30_000 });

    hub.add(socket);
    socket.emit(
      "message",
      JSON.stringify({
        action: "subscribe",
        events: ["TRADE"],
      }),
    );

    hub.publish(trade);

    const messages = socket.sent.map((message: string) => JSON.parse(message));

    expect(messages[1]).toEqual({
      type: "SUBSCRIPTION_UPDATED",
      subscriptions: ["TRADE"],
    });
    expect(messages[2]).toEqual({
      type: "TRADE",
      eventId: "event-1",
      requestId: "request-1",
      timestamp: "2026-10-02T12:00:00.000Z",
      payload: trade.payload,
    });
  });

  test("preserves analytics event and request IDs for WebSocket consumers", () => {
    const socket = createSocket();
    const hub = createWebSocketHub({ maxQueueSize: 8, heartbeatIntervalMs: 30_000 });

    hub.add(socket);
    socket.emit(
      "message",
      JSON.stringify({
        action: "subscribe",
        events: ["ANALYTICS_UPDATE"],
      }),
    );

    hub.publish(analyticsUpdate);

    expect(JSON.parse(socket.sent[2])).toEqual({
      type: "ANALYTICS_UPDATE",
      eventId: "analytics-event-1",
      requestId: "trade-request-1",
      timestamp: "2026-10-02T12:00:01.000Z",
      payload: analyticsUpdate.payload,
    });
  });

  test("rejects unexpected subscription fields", () => {
    const socket = createSocket();
    const hub = createWebSocketHub({ maxQueueSize: 8, heartbeatIntervalMs: 30_000 });

    hub.add(socket);
    socket.emit(
      "message",
      JSON.stringify({
        action: "subscribe",
        events: ["TRADE"],
        extra: true,
      }),
    );

    expect(JSON.parse(socket.sent[1])).toEqual({
      type: "ERROR",
      error: {
        code: "INVALID_CLIENT_MESSAGE",
        message: "WebSocket message contains unsupported field 'extra'",
      },
    });
  });

  test("rejects duplicate subscription events", () => {
    const socket = createSocket();
    const hub = createWebSocketHub({ maxQueueSize: 8, heartbeatIntervalMs: 30_000 });

    hub.add(socket);
    socket.emit(
      "message",
      JSON.stringify({
        action: "subscribe",
        events: ["TRADE", "TRADE"],
      }),
    );

    expect(JSON.parse(socket.sent[1])).toEqual({
      type: "ERROR",
      error: {
        code: "INVALID_CLIENT_MESSAGE",
        message: "WebSocket events must not contain duplicate values",
      },
    });
  });

  test("rejects unsupported subscription events", () => {
    const socket = createSocket();
    const hub = createWebSocketHub({ maxQueueSize: 8, heartbeatIntervalMs: 30_000 });

    hub.add(socket);
    socket.emit(
      "message",
      JSON.stringify({
        action: "subscribe",
        events: ["BOOK_SNAPSHOT"],
      }),
    );

    expect(JSON.parse(socket.sent[1])).toEqual({
      type: "ERROR",
      error: {
        code: "INVALID_CLIENT_MESSAGE",
        message: "WebSocket message contains an unsupported event type",
      },
    });
  });

  test("removes a client when its queue exceeds the configured limit", () => {
    const socket = createSocket();
    const hub = createWebSocketHub({ maxQueueSize: 0, heartbeatIntervalMs: 30_000 });

    hub.add(socket);

    expect(hub.size()).toBe(0);
  });
});
