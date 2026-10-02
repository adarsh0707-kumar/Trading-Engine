import { createServer, type Server } from "node:net";

import { afterEach, describe, expect, test } from "bun:test";

import { createEngineEventClient } from "../src/engine/engine-event-client.ts";

function frame(payload: string): Buffer {
  const body = Buffer.from(payload, "utf8");
  const result = Buffer.allocUnsafe(4 + body.length);

  result.writeUInt32BE(body.length, 0);
  body.copy(result, 4);

  return result;
}

function tradeMessage(): string {
  return JSON.stringify({
    type: "TRADE",
    request_id: "trade-00000001-buy-1-sell-1",
    timestamp: "2026-10-02T12:00:00.000Z",
    payload: JSON.stringify({
      symbol: "SIM",
      price: 100.25,
      quantity: 10,
      taker_order_id: "buy-1",
      maker_order_id: "sell-1",
      taker_side: "BUY",
      buy_order_id: "buy-1",
      sell_order_id: "sell-1",
    }),
  });
}

const servers: Server[] = [];

afterEach(async () => {
  await Promise.all(
    servers.map(
      (server) =>
        new Promise<void>((resolve) => {
          if (!server.listening) {
            resolve();
            return;
          }

          server.close(() => resolve());
        }),
    ),
  );

  servers.length = 0;
});

describe("engine event client", () => {
  test("normalizes live TRADE frames and publishes them through the callback", async () => {
    const server = createServer((socket) => {
      socket.write(frame(tradeMessage()));
    });

    servers.push(server);

    await new Promise<void>((resolve) => {
      server.listen(0, "127.0.0.1", () => resolve());
    });

    const address = server.address();

    if (address === null || typeof address === "string") {
      throw new Error("Test server did not expose an address");
    }

    const events: unknown[] = [];

    const client = createEngineEventClient({
      host: "127.0.0.1",
      port: address.port,
      connectTimeoutMs: 1000,
      reconnectInitialDelayMs: 10,
      reconnectMaxDelayMs: 20,
      reconnectMaxAttempts: 1,
      onEvent: (event) => {
        events.push(event);
      },
    });

    client.start();

    await new Promise<void>((resolve) => {
      const deadline = Date.now() + 1000;

      const check = (): void => {
        if (events.length === 1 || Date.now() >= deadline) {
          resolve();
          return;
        }

        setTimeout(check, 5);
      };

      check();
    });

    client.stop();

    expect(events).toHaveLength(1);
    expect(events[0]).toEqual({
      type: "TRADE",
      eventId: "trade-00000001-buy-1-sell-1",
      tradeId: "trade-00000001-buy-1-sell-1",
      requestId: "trade-00000001-buy-1-sell-1",
      timestamp: "2026-10-02T12:00:00.000Z",
      payload: {
        symbol: "SIM",
        price: 100.25,
        quantity: 10,
        takerOrderId: "buy-1",
        makerOrderId: "sell-1",
        takerSide: "BUY",
        buyOrderId: "buy-1",
        sellOrderId: "sell-1",
      },
    });
  });

  test("responds to engine HEARTBEAT messages", async () => {
    const server = createServer((socket) => {
      socket.write(
        frame(
          JSON.stringify({
            type: "HEARTBEAT",
            request_id: "heartbeat-1",
            timestamp: "2026-10-02T12:00:00.000Z",
            payload: "PING",
          }),
        ),
      );

      socket.once("data", (data) => {
        const payloadSize = data.readUInt32BE(0);
        const payload = data.subarray(4, 4 + payloadSize).toString("utf8");
        const message = JSON.parse(payload) as Record<string, unknown>;

        expect(message).toEqual({
          type: "HEARTBEAT",
          request_id: "heartbeat-1",
          timestamp: "2026-10-02T12:00:00.000Z",
          payload: "OK",
        });
      });
    });

    servers.push(server);

    await new Promise<void>((resolve) => {
      server.listen(0, "127.0.0.1", () => resolve());
    });

    const address = server.address();

    if (address === null || typeof address === "string") {
      throw new Error("Test server did not expose an address");
    }

    const client = createEngineEventClient({
      host: "127.0.0.1",
      port: address.port,
      connectTimeoutMs: 1000,
      reconnectInitialDelayMs: 10,
      reconnectMaxDelayMs: 20,
      reconnectMaxAttempts: 1,
      onEvent: () => {},
    });

    client.start();

    await new Promise((resolve) => setTimeout(resolve, 100));
    client.stop();

    expect(client.isConnected()).toBe(false);
  });

  test("stops reconnecting after the configured attempt limit", async () => {
    let connecting = 0;

    const client = createEngineEventClient({
      host: "127.0.0.1",
      port: 1,
      connectTimeoutMs: 50,
      reconnectInitialDelayMs: 10,
      reconnectMaxDelayMs: 10,
      reconnectMaxAttempts: 2,
      onEvent: () => {},
      onStateChange: (state) => {
        if (state === "connecting") {
          connecting += 1;
        }
      },
    });

    client.start();

    await new Promise((resolve) => setTimeout(resolve, 100));
    client.stop();

    expect(connecting).toBeGreaterThanOrEqual(1);
    expect(connecting).toBeLessThanOrEqual(3);
  });
});
