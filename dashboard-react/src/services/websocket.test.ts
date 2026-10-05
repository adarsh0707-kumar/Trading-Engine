import { describe, expect, test } from "bun:test";

import { createGatewayWebSocketClient } from "./websocket";
import type { GatewayWebSocket } from "../types/websocket";

class FakeWebSocket implements GatewayWebSocket {
  static readonly instances: FakeWebSocket[] = [];

  readonly readyState = 1;
  onopen: (() => void) | null = null;
  onmessage: ((event: { data: unknown }) => void) | null = null;
  onerror: (() => void) | null = null;
  onclose: (() => void) | null = null;
  readonly sent: string[] = [];
  closed = false;
  readonly url: string;

  constructor(url: string) {
    this.url = url;
    FakeWebSocket.instances.push(this);
  }

  send(data: string): void {
    this.sent.push(data);
  }

  close(): void {
    this.closed = true;
    this.onclose?.();
  }

  open(): void {
    this.onopen?.();
  }

  message(data: unknown): void {
    this.onmessage?.({ data });
  }

  fail(): void {
    this.onerror?.();
  }

  remoteClose(): void {
    this.onclose?.();
  }
}

function resetSockets(): void {
  FakeWebSocket.instances.length = 0;
}

describe("Gateway WebSocket client", () => {
  test("builds the WebSocket URL and opens a connection", () => {
    resetSockets();
    const states: string[] = [];
    const client = createGatewayWebSocketClient({
      baseUrl: "https://gateway.test/",
      path: "/ws",
      webSocketFactory: (url) => new FakeWebSocket(url),
      reconnect: false,
      onStateChange: (state) => states.push(state),
    });

    client.connect();

    expect(FakeWebSocket.instances[0]?.url).toBe("wss://gateway.test/ws");
    expect(client.getState()).toBe("connecting");

    FakeWebSocket.instances[0]?.open();

    expect(client.getState()).toBe("open");
    expect(states).toEqual(["connecting", "open"]);
  });

  test("subscribes on an open socket and preserves subscriptions across reconnects", async () => {
    resetSockets();
    const client = createGatewayWebSocketClient({
      baseUrl: "http://gateway.test",
      reconnectInitialDelayMs: 1,
      reconnectMaxDelayMs: 1,
      maxReconnectAttempts: 2,
      webSocketFactory: (url) => new FakeWebSocket(url),
    });

    client.subscribe(["TRADE", "TRADE", "ANALYTICS_UPDATE"]);
    client.connect();

    const first = FakeWebSocket.instances[0];
    first?.open();

    expect(first?.sent).toEqual([
      JSON.stringify({
        action: "subscribe",
        events: ["TRADE", "ANALYTICS_UPDATE"],
      }),
    ]);

    first?.remoteClose();
    await Bun.sleep(5);

    const second = FakeWebSocket.instances[1];
    expect(second).toBeDefined();

    second?.open();

    expect(second?.sent).toEqual([
      JSON.stringify({
        action: "subscribe",
        events: ["TRADE", "ANALYTICS_UPDATE"],
      }),
    ]);
  });

  test("sends unsubscribe messages and stops tracking removed subscriptions", () => {
    resetSockets();
    const client = createGatewayWebSocketClient({
      webSocketFactory: (url) => new FakeWebSocket(url),
    });

    client.connect();
    const socket = FakeWebSocket.instances[0];
    socket?.open();

    client.subscribe(["TRADE", "RISK_EVENT"]);
    client.unsubscribe(["TRADE"]);

    expect(socket?.sent).toEqual([
      JSON.stringify({ action: "subscribe", events: ["TRADE", "RISK_EVENT"] }),
      JSON.stringify({ action: "unsubscribe", events: ["TRADE"] }),
    ]);
  });

  test("delivers typed gateway events and reports malformed messages", () => {
    resetSockets();
    const events: unknown[] = [];
    const errors: unknown[] = [];
    const client = createGatewayWebSocketClient({
      webSocketFactory: (url) => new FakeWebSocket(url),
      onEvent: (event) => events.push(event),
      onError: (error) => errors.push(error),
    });

    client.connect();
    const socket = FakeWebSocket.instances[0];
    socket?.open();

    socket?.message(JSON.stringify({
      type: "TRADE",
      eventId: "event-1",
      requestId: "request-1",
      timestamp: "2026-10-05T10:00:00.000Z",
      payload: {
        symbol: "SIM",
        price: 100.25,
        quantity: 2,
        takerOrderId: "buy-1",
        makerOrderId: "sell-1",
        takerSide: "BUY",
        buyOrderId: "buy-1",
        sellOrderId: "sell-1",
      },
    }));
    socket?.message("{not-json");

    expect(events).toHaveLength(1);
    expect(events[0]).toMatchObject({
      type: "TRADE",
      eventId: "event-1",
      requestId: "request-1",
    });
    expect(errors).toEqual([{
      code: "INVALID_MESSAGE",
      message: "Gateway WebSocket message contains invalid JSON",
    }]);
  });

  test("ignores gateway control messages and reports connection errors", () => {
    resetSockets();
    const errors: unknown[] = [];
    const events: unknown[] = [];
    const client = createGatewayWebSocketClient({
      reconnect: false,
      webSocketFactory: (url) => new FakeWebSocket(url),
      onError: (error) => errors.push(error),
      onEvent: (event) => events.push(event),
    });

    client.connect();
    const socket = FakeWebSocket.instances[0];
    socket?.open();

    socket?.message(JSON.stringify({
      type: "CONNECTION_READY",
      subscriptions: [],
    }));
    socket?.message(JSON.stringify({
      type: "SUBSCRIPTION_UPDATED",
      subscriptions: ["TRADE"],
    }));
    socket?.fail();

    expect(events).toHaveLength(0);
    expect(errors).toEqual([{
      code: "CONNECTION_ERROR",
      message: "Gateway WebSocket connection failed",
    }]);
  });

  test("disconnects intentionally without scheduling a reconnect", async () => {
    resetSockets();
    const states: string[] = [];
    const client = createGatewayWebSocketClient({
      reconnectInitialDelayMs: 1,
      reconnectMaxDelayMs: 1,
      webSocketFactory: (url) => new FakeWebSocket(url),
      onStateChange: (state) => states.push(state),
    });

    client.connect();
    const socket = FakeWebSocket.instances[0];
    socket?.open();
    client.disconnect();

    await Bun.sleep(5);

    expect(socket?.closed).toBe(true);
    expect(FakeWebSocket.instances).toHaveLength(1);
    expect(client.getState()).toBe("closed");
    expect(states.at(-1)).toBe("closed");
  });
});
