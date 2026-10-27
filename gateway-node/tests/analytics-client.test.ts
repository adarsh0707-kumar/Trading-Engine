import { createServer, type Server } from "node:net";

import { afterEach, describe, expect, test } from "bun:test";

import { createAnalyticsClient } from "../src/analytics/analytics-client.ts";

function decodeFrame(data: Buffer): Record<string, unknown> {
  const payloadSize = data.readUInt32BE(0);
  const payload = data.subarray(4, 4 + payloadSize).toString("utf8");
  return JSON.parse(payload) as Record<string, unknown>;
}

function tradeEvent() {
  return {
    type: "TRADE" as const,
    eventId: "trade-00000001-buy-1-sell-1",
    tradeId: "trade-00000001-buy-1-sell-1",
    requestId: "trade-00000001-buy-1-sell-1",
    timestamp: "2026-10-02T12:00:01.000Z",
    payload: {
      symbol: "SIM",
      price: 100.25,
      quantity: 10,
      takerOrderId: "buy-1",
      makerOrderId: "sell-1",
      takerSide: "BUY" as const,
      buyOrderId: "buy-1",
      sellOrderId: "sell-1",
    },
  };
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

describe("analytics client", () => {
  test("connects and sends a versioned TRADE frame", async () => {
    let received: Record<string, unknown> | undefined;

    const server = createServer((socket) => {
      socket.once("data", (data) => {
        received = decodeFrame(Buffer.from(data));
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

    const client = createAnalyticsClient({
      host: "127.0.0.1",
      port: address.port,
      connectTimeoutMs: 1000,
      reconnectInitialDelayMs: 10,
      reconnectMaxDelayMs: 20,
      reconnectMaxAttempts: 1,
      maxQueueSize: 10,
    });

    client.start();

    const deadline = Date.now() + 1000;
    while (received === undefined && Date.now() < deadline) {
      await new Promise((resolve) => setTimeout(resolve, 5));
    }

    expect(client.sendTrade(tradeEvent())).toBe(true);

    const sendDeadline = Date.now() + 1000;
    while (received === undefined && Date.now() < sendDeadline) {
      await new Promise((resolve) => setTimeout(resolve, 5));
    }

    client.stop();

    expect(received).toEqual({
      version: 1,
      type: "TRADE",
      event_id: "trade-00000001-buy-1-sell-1",
      request_id: "trade-00000001-buy-1-sell-1",
      timestamp: "2026-10-02T12:00:01.000Z",
      payload: JSON.stringify({
        trade_id: "trade-00000001-buy-1-sell-1",
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
  });

  test("queues trades while disconnected and flushes after reconnect", async () => {
    let received = 0;

    const server = createServer((socket) => {
      socket.on("data", (data) => {
        received += 1;
        expect(decodeFrame(Buffer.from(data)).type).toBe("TRADE");
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

    const client = createAnalyticsClient({
      host: "127.0.0.1",
      port: address.port,
      connectTimeoutMs: 1000,
      reconnectInitialDelayMs: 10,
      reconnectMaxDelayMs: 20,
      reconnectMaxAttempts: 2,
      maxQueueSize: 2,
    });

    expect(client.sendTrade(tradeEvent())).toBe(true);
    expect(client.getQueueSize()).toBe(1);

    client.start();

    const deadline = Date.now() + 1000;
    while (received !== 1 && Date.now() < deadline) {
      await new Promise((resolve) => setTimeout(resolve, 5));
    }

    client.stop();

    expect(received).toBe(1);
    expect(client.getQueueSize()).toBe(0);
  });

  test("reconnects after analytics disconnect and flushes queued trades", async () => {
    let connections = 0;
    const receivedTradeIds: string[] = [];
    const states: string[] = [];
    let releaseReconnect!: () => void;
    const reconnectGate = new Promise<void>((resolve) => {
      releaseReconnect = resolve;
    });

    const server = createServer((socket) => {
      const connectionNumber = ++connections;
      let buffer = Buffer.alloc(0);

      socket.on("data", (chunk) => {
        buffer = Buffer.concat([buffer, Buffer.from(chunk)]);

        while (buffer.length >= 4) {
          const payloadSize = buffer.readUInt32BE(0);
          const frameSize = payloadSize + 4;
          if (buffer.length < frameSize) return;

          const message = decodeFrame(buffer.subarray(0, frameSize));
          buffer = buffer.subarray(frameSize);
          receivedTradeIds.push(String(message.event_id));

          if (connectionNumber === 1) {
            socket.destroy();
            return;
          }
        }
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

    const client = createAnalyticsClient({
      host: "127.0.0.1",
      port: address.port,
      connectTimeoutMs: 1000,
      reconnectInitialDelayMs: 10,
      reconnectMaxDelayMs: 20,
      reconnectMaxAttempts: 5,
      maxQueueSize: 2,
      onStateChange: (state) => states.push(state),
      onConnected: async () => {
        if (connections >= 2) {
          await reconnectGate;
        }
      },
    });

    const waitFor = async (
      predicate: () => boolean,
      timeoutMs = 1500,
    ): Promise<void> => {
      const deadline = Date.now() + timeoutMs;
      while (!predicate() && Date.now() < deadline) {
        await new Promise((resolve) => setTimeout(resolve, 5));
      }
      expect(predicate()).toBe(true);
    };

    try {
      client.start();
      await waitFor(() => client.isConnected() && connections === 1);

      expect(client.sendTrade(tradeEvent())).toBe(true);
      await waitFor(() => receivedTradeIds.length === 1);
      await waitFor(() => client.getState() === "disconnected");

      const queuedTrade = {
        ...tradeEvent(),
        eventId: "trade-2",
        tradeId: "trade-2",
        requestId: "trade-2",
      };
      expect(client.sendTrade(queuedTrade)).toBe(true);
      expect(client.getQueueSize()).toBe(1);

      await waitFor(() => client.isConnected() && connections >= 2);
      await new Promise((resolve) => setTimeout(resolve, 30));
      expect(receivedTradeIds).toHaveLength(1);

      releaseReconnect();
      await waitFor(() => receivedTradeIds.length === 2);

      expect(receivedTradeIds).toEqual([
        "trade-00000001-buy-1-sell-1",
        "trade-2",
      ]);
      expect(connections).toBeGreaterThanOrEqual(2);
      expect(client.getQueueSize()).toBe(0);
      expect(states).toContain("disconnected");
      expect(states).toContain("connected");
    } finally {
      client.stop();
    }
  });

  test("rejects trades when the bounded queue is full", () => {
    const errors: Error[] = [];
    const healthEvents: string[] = [];

    const client = createAnalyticsClient({
      host: "127.0.0.1",
      port: 1,
      connectTimeoutMs: 1000,
      reconnectInitialDelayMs: 10,
      reconnectMaxDelayMs: 20,
      reconnectMaxAttempts: 0,
      maxQueueSize: 1,
      onError: (error) => {
        errors.push(error);
      },
      onHealthEvent: ({ type }) => {
        healthEvents.push(type);
      },
    });

    expect(client.sendTrade(tradeEvent())).toBe(true);
    expect(client.sendTrade(tradeEvent())).toBe(false);
    expect(client.getQueueSize()).toBe(1);
    expect(errors[0]?.name).toBe("GatewayFailure");
    expect((errors[0] as { category?: string }).category).toBe("queue_overflow");
    expect((errors[0] as { recoverable?: boolean }).recoverable).toBe(true);
    expect(healthEvents).toEqual(["queue_overflow"]);
  });
});


test("parses persistence acknowledgements from analytics", async () => {
  let receivedAck: Record<string, unknown> | undefined;

  const server = createServer((socket) => {
    socket.once("data", () => {
      const payload = Buffer.from(
        JSON.stringify({
          version: 1,
          type: "TRADE_ACK",
          event_id: "trade-00000001-buy-1-sell-1",
          request_id: "trade-00000001-buy-1-sell-1",
          status: "persisted",
        }),
        "utf8",
      );
      const response = Buffer.alloc(4 + payload.length);
      response.writeUInt32BE(payload.length, 0);
      payload.copy(response, 4);
      socket.write(response);
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

  const client = createAnalyticsClient({
    host: "127.0.0.1",
    port: address.port,
    connectTimeoutMs: 1000,
    reconnectInitialDelayMs: 10,
    reconnectMaxDelayMs: 20,
    reconnectMaxAttempts: 1,
    maxQueueSize: 10,
    onTradeAck: (message) => {
      receivedAck = message as unknown as Record<string, unknown>;
    },
  });

  client.start();
  try {
    const deadline = Date.now() + 1000;
    while (!client.isConnected() && Date.now() < deadline) {
      await new Promise((resolve) => setTimeout(resolve, 5));
    }

    expect(client.sendTrade(tradeEvent())).toBe(true);

    const ackDeadline = Date.now() + 1000;
    while (receivedAck === undefined && Date.now() < ackDeadline) {
      await new Promise((resolve) => setTimeout(resolve, 5));
    }

    expect(receivedAck).toEqual({
      version: 1,
      type: "TRADE_ACK",
      event_id: "trade-00000001-buy-1-sell-1",
      request_id: "trade-00000001-buy-1-sell-1",
      status: "persisted",
    });
  } finally {
    client.stop();
  }
});
